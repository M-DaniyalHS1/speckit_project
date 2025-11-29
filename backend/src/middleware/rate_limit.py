"""API rate limiting and monitoring middleware for the AI-Enhanced Interactive Book Agent.

This module provides rate limiting capabilities to prevent API abuse and includes
monitoring functionality to track API usage patterns.
"""
import time
import asyncio
from collections import defaultdict, deque
from typing import Dict, Optional, Callable, Awaitable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.background import BackgroundTask
from backend.src.config import settings
from backend.src.utils.logging import log_api_call, get_logger


logger = get_logger("rate_limit")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits on API endpoints."""

    def __init__(
        self,
        app,
        default_limits: Dict[str, int] = None,  # {time_period: max_requests}
        endpoint_limits: Dict[str, Dict[str, int]] = None,  # {endpoint_pattern: {time_period: max_requests}}
        user_limits: Dict[str, int] = None,  # {user_type: {time_period: max_requests}}
        track_usage: bool = True
    ):
        """Initialize the rate limiting middleware.

        Args:
            app: The FastAPI application
            default_limits: Default rate limits per time period (seconds) {time_period: max_requests}
            endpoint_limits: Endpoint-specific rate limits {endpoint_pattern: {time_period: max_requests}}
            user_limits: User-type-specific rate limits
            track_usage: Whether to track API usage for monitoring
        """
        super().__init__(app)
        self.default_limits = default_limits or {60: 100}  # 100 requests per minute by default
        self.endpoint_limits = endpoint_limits or {}
        self.user_limits = user_limits or {
            "free": {60: 50},      # 50 requests per minute for free users
            "premium": {60: 500},  # 500 requests per minute for premium users
            "admin": {60: 1000}    # 1000 requests per minute for admin users
        }
        self.track_usage = track_usage

        # Storage for rate limit tracking
        self.requests_by_ip: Dict[str, deque] = defaultdict(deque)  # IP-based tracking
        self.requests_by_endpoint: Dict[str, deque] = defaultdict(deque)  # Endpoint tracking
        self.requests_by_user: Dict[str, deque] = defaultdict(deque)  # User-based tracking

        # Monitoring statistics
        self.stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "requests_by_endpoint": defaultdict(int),
            "requests_by_user": defaultdict(int),
            "requests_by_ip": defaultdict(int),
            "start_time": time.time()
        }

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request and enforce rate limits.

        Args:
            request: Incoming request
            call_next: Next middleware or endpoint in the chain

        Returns:
            API response
        """
        client_ip = self._get_client_ip(request)
        endpoint = request.url.path
        user_id = self._get_user_id(request)

        # Check rate limits
        if not await self._is_allowed(client_ip, endpoint, user_id):
            # Increment blocked counter
            self.stats["blocked_requests"] += 1
            
            # Create a detailed error response
            limit_info = self._get_limit_info(client_ip, endpoint, user_id)
            retry_after = self._calculate_retry_after(client_ip)
            
            error_detail = {
                "error": "Rate limit exceeded",
                "detail": f"Too many requests from this {self._get_identifier_type(client_ip, user_id)}",
                "retry_after_seconds": retry_after,
                "limits_applied": limit_info
            }
            
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=error_detail,
            )
            
            response.headers["Retry-After"] = str(int(retry_after))
            response.headers["X-RateLimit-Limit"] = str(limit_info.get("max_requests", 0))
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + retry_after))
            
            return response

        # Track request for rate limiting
        await self._track_request(client_ip, endpoint, user_id)

        # Track for monitoring (non-blocking)
        if self.track_usage:
            self._update_monitoring_stats(client_ip, endpoint, user_id)

        # Continue with the request
        start_time = time.time()
        try:
            response = await call_next(request)
        finally:
            # Add response headers with rate limit information
            if self.track_usage:
                response = await self._add_rate_limit_headers(response, client_ip, endpoint, user_id)
                
                # Log request details for monitoring
                await self._log_request_metrics(
                    request, response, time.time() - start_time, client_ip
                )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request.

        Args:
            request: Incoming request

        Returns:
            Client IP address
        """
        # Check for forwarded IP headers (for use behind proxies/load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in case of multiple (client, proxy1, proxy2, ...)
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Use direct client IP if no forwarded headers
        return request.client.host if request.client else "unknown"

    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request (if authenticated).

        Args:
            request: Incoming request

        Returns:
            User ID if available, None otherwise
        """
        # Check if user is attached to request state (after authentication)
        if hasattr(request.state, 'user_id'):
            return str(request.state.user_id)
        
        # Check for user ID in headers (for internal calls)
        user_id = request.headers.get("X-User-ID")
        return user_id

    def _get_limit_config(self, ip: str, endpoint: str, user_id: Optional[str]) -> Dict[str, int]:
        """Get appropriate rate limit configuration based on context.

        Args:
            ip: Client IP address
            endpoint: Request endpoint
            user_id: User ID (if authenticated)

        Returns:
            Rate limit configuration {time_period: max_requests}
        """
        # Priority order: User limits > Endpoint limits > Default limits

        # If user is authenticated, check user-specific limits
        if user_id:
            # Determine user type and apply corresponding limits
            user_type = self._get_user_type(user_id)
            if user_type in self.user_limits:
                return self.user_limits[user_type]

        # Check for endpoint-specific limits
        for pattern, limits in self.endpoint_limits.items():
            if endpoint.startswith(pattern):
                return limits

        # Fall back to default limits
        return self.default_limits

    def _get_user_type(self, user_id: str) -> str:
        """Determine user type based on user ID or other criteria.

        Args:
            user_id: User ID

        Returns:
            User type ('free', 'premium', 'admin', etc.)
        """
        # In a real implementation, this would check the user's subscription/status in the database
        # For now, default to 'free' for all users
        return "free"  # Default fallback

    async def _is_allowed(self, ip: str, endpoint: str, user_id: Optional[str]) -> bool:
        """Check if a request is within rate limits.

        Args:
            ip: Client IP address
            endpoint: Request endpoint
            user_id: User ID (if authenticated)

        Returns:
            True if request is allowed, False if rate limited
        """
        limits = self._get_limit_config(ip, endpoint, user_id)

        # Check all time windows in the limits configuration
        current_time = time.time()

        # Check IP-based rate limit
        if not self._check_rate_limit(self.requests_by_ip[ip], limits, current_time):
            return False

        # Check endpoint-based rate limit
        if not self._check_rate_limit(self.requests_by_endpoint[endpoint], limits, current_time):
            return False

        # Check user-based rate limit (if user is identified)
        if user_id and not self._check_rate_limit(self.requests_by_user[user_id], limits, current_time):
            return False

        return True

    def _check_rate_limit(self, request_times: deque, limits: Dict[str, int], current_time: float) -> bool:
        """Check if requests in the time window exceed the limit.

        Args:
            request_times: Deque of request timestamps
            limits: Rate limits configuration {time_period: max_requests}
            current_time: Current timestamp

        Returns:
            True if within limits, False if exceeded
        """
        # Clean out old requests outside the time window
        time_window = max(limits.keys())  # Use the largest time window for cleaning
        while request_times and current_time - request_times[0] > time_window:
            request_times.popleft()

        # Check if any time window is exceeded
        for time_period, max_requests in limits.items():
            # Count requests within this time period
            recent_requests = sum(1 for req_time in request_times if current_time - req_time <= time_period)
            if recent_requests >= max_requests:
                return False

        return True

    async def _track_request(self, ip: str, endpoint: str, user_id: Optional[str]):
        """Track a request for rate limiting purposes.

        Args:
            ip: Client IP address
            endpoint: Request endpoint
            user_id: User ID (if authenticated)
        """
        current_time = time.time()

        # Track IP-based requests
        self.requests_by_ip[ip].append(current_time)

        # Track endpoint-based requests
        self.requests_by_endpoint[endpoint].append(current_time)

        # Track user-based requests (if user is identified)
        if user_id:
            self.requests_by_user[user_id].append(current_time)

    def _calculate_retry_after(self, ip: str) -> float:
        """Calculate when the client can retry after exceeding limits.

        Args:
            ip: Client IP address

        Returns:
            Seconds until client can retry
        """
        # For now, return a default wait time
        # In a real implementation, this would calculate based on the specific rate limit window
        return 60  # 60 seconds default retry period

    def _get_identifier_type(self, ip: str, user_id: Optional[str]) -> str:
        """Get the type of identifier that exceeded the limit.

        Args:
            ip: Client IP address
            user_id: User ID (if authenticated)

        Returns:
            Type of identifier ('IP address', 'user', etc.)
        """
        return "user" if user_id else "IP address"

    def _update_monitoring_stats(self, ip: str, endpoint: str, user_id: Optional[str]):
        """Update monitoring statistics for the request.

        Args:
            ip: Client IP address
            endpoint: Request endpoint
            user_id: User ID (if authenticated)
        """
        self.stats["total_requests"] += 1
        self.stats["requests_by_endpoint"][endpoint] += 1
        if user_id:
            self.stats["requests_by_user"][user_id] += 1
        self.stats["requests_by_ip"][ip] += 1

    async def _add_rate_limit_headers(self, response: Response, ip: str, endpoint: str, user_id: Optional[str]):
        """Add rate limit headers to the response.

        Args:
            response: API response
            ip: Client IP address
            endpoint: Request endpoint
            user_id: User ID (if authenticated)

        Returns:
            Response with rate limit headers
        """
        limits = self._get_limit_config(ip, endpoint, user_id)
        max_requests = max(limits.values()) if limits else 100

        # Calculate remaining requests
        current_time = time.time()
        if ip in self.requests_by_ip:
            requests_in_window = len([
                req_time for req_time in self.requests_by_ip[ip] 
                if current_time - req_time <= 60  # Using 60 sec window as example
            ])
            remaining = max(0, max_requests - requests_in_window)
        else:
            remaining = max_requests

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))

        return response

    def _get_limit_info(self, ip: str, endpoint: str, user_id: Optional[str]) -> Dict[str, any]:
        """Get detailed information about applied rate limits.

        Args:
            ip: Client IP address
            endpoint: Request endpoint
            user_id: User ID (if authenticated)

        Returns:
            Dictionary with limit configuration details
        """
        limits = self._get_limit_config(ip, endpoint, user_id)
        max_requests = max(limits.values()) if limits else 100
        time_window = max(limits.keys()) if limits else 60

        return {
            "max_requests": max_requests,
            "time_window_seconds": time_window,
            "identifier": user_id if user_id else ip,
            "identifier_type": "user_id" if user_id else "ip_address"
        }

    async def _log_request_metrics(self, request: Request, response: Response, duration: float, client_ip: str):
        """Log detailed request metrics for monitoring purposes.

        Args:
            request: Original request
            response: Response sent
            duration: Request processing duration in seconds
            client_ip: Client IP address
        """
        try:
            user_id = self._get_user_id(request) or "anonymous"
            endpoint = request.url.path
            method = request.method
            status_code = response.status_code

            # Log performance metric
            from backend.src.utils.logging import logger_manager
            logger_manager.log_performance(
                logger,
                f"API Request: {method} {endpoint}",
                duration,
                {
                    "client_ip": client_ip,
                    "user_id": user_id,
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": status_code
                }
            )
        except Exception as e:
            logger.error(f"Error logging request metrics: {str(e)}")

    async def get_stats(self) -> Dict[str, any]:
        """Get current rate limiting and monitoring statistics.

        Returns:
            Dictionary with current statistics
        """
        current_time = time.time()
        uptime = current_time - self.stats["start_time"]
        
        return {
            "uptime_seconds": uptime,
            "total_requests": self.stats["total_requests"],
            "blocked_requests": self.stats["blocked_requests"],
            "block_percentage": (
                (self.stats["blocked_requests"] / self.stats["total_requests"]) * 100
                if self.stats["total_requests"] > 0 else 0
            ),
            "active_ips": len(self.requests_by_ip),
            "requests_by_endpoint": dict(self.stats["requests_by_endpoint"]),
            "requests_by_user": dict(self.stats["requests_by_user"]),
            "requests_by_ip": dict(self.stats["requests_by_ip"]),
        }


# Global instance of the rate limiting middleware
rate_limit_middleware = None


def init_rate_limit_middleware(app, settings_obj=None):
    """Initialize the rate limiting middleware with the FastAPI app.

    Args:
        app: FastAPI application instance
        settings_obj: Settings object with rate limit configurations (optional)
    """
    global rate_limit_middleware
    
    if settings_obj is None:
        from backend.src.config import settings as settings_obj
    
    # Configure default limits based on settings
    default_limits = {60: getattr(settings_obj, 'api_rate_limit', 100)}  # requests per minute
    
    # Endpoint-specific limits (customize as needed)
    endpoint_limits = {
        "/api/search": {60: 50},      # Search endpoints - lower limit
        "/api/explanations": {60: 30}, # Explanation endpoints - lower limit 
        "/api/summaries": {60: 20},   # Summary endpoints - lower limit
    }
    
    # Initialize the middleware
    rate_limit_middleware = RateLimitMiddleware(
        app=app,
        default_limits=default_limits,
        endpoint_limits=endpoint_limits
    )
    
    return rate_limit_middleware