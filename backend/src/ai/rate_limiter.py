"""Rate limiting module for AI API calls in the AI-Enhanced Interactive Book Agent.

This module implements rate limiting for AI API calls to manage costs and prevent abuse.
"""
import time
import asyncio
from collections import defaultdict, deque
from typing import Dict, Optional
from fastapi import HTTPException, status
from backend.src.config import settings


class AILimitExceededException(Exception):
    """Exception raised when AI API usage limits are exceeded."""
    pass


class AIRateLimiter:
    """Rate limiter for AI API calls."""
    
    def __init__(self):
        """Initialize the rate limiter."""
        # Track requests per API key
        self.requests_by_api_key: Dict[str, deque] = defaultdict(deque)
        
        # Track requests per user
        self.requests_by_user: Dict[str, deque] = defaultdict(deque)
        
        # Track requests per endpoint
        self.requests_by_endpoint: Dict[str, deque] = defaultdict(deque)
        
        # Global request tracking
        self.global_requests: deque = deque()
        
        # Configuration from settings
        self.max_requests_per_minute = settings.api_rate_limit
        self.max_requests_per_minute_per_user = 20  # Reasonable default
        self.time_window = 60  # 60 seconds
    
    def _clean_old_requests(self, request_deque: deque, now: float):
        """Remove requests older than the time window.
        
        Args:
            request_deque: Deque of request timestamps
            now: Current timestamp
        """
        while request_deque and now - request_deque[0] > self.time_window:
            request_deque.popleft()
    
    def _check_limit(self, request_deque: deque, limit: int, now: float) -> bool:
        """Check if a specific limit is exceeded.
        
        Args:
            request_deque: Deque of request timestamps
            limit: Maximum number of requests allowed
            now: Current timestamp
            
        Returns:
            True if within limit, False otherwise
        """
        self._clean_old_requests(request_deque, now)
        return len(request_deque) < limit
    
    def _add_request(self, request_deque: deque, now: float):
        """Add a request timestamp to the deque.
        
        Args:
            request_deque: Deque of request timestamps
            now: Current timestamp
        """
        request_deque.append(now)
    
    async def check_api_key_limit(self, api_key: str) -> bool:
        """Check if the API key is within its rate limit.
        
        Args:
            api_key: The API key making the request
            
        Returns:
            True if within limit, False otherwise
        """
        now = time.time()
        return self._check_limit(
            self.requests_by_api_key[api_key], 
            self.max_requests_per_minute, 
            now
        )
    
    async def check_user_limit(self, user_id: str) -> bool:
        """Check if the user is within their rate limit.
        
        Args:
            user_id: The ID of the user making the request
            
        Returns:
            True if within limit, False otherwise
        """
        now = time.time()
        return self._check_limit(
            self.requests_by_user[user_id], 
            self.max_requests_per_minute_per_user, 
            now
        )
    
    async def check_endpoint_limit(self, endpoint: str) -> bool:
        """Check if the endpoint is within its rate limit.
        
        Args:
            endpoint: The API endpoint being called
            
        Returns:
            True if within limit, False otherwise
        """
        now = time.time()
        return self._check_limit(
            self.requests_by_endpoint[endpoint], 
            self.max_requests_per_minute, 
            now
        )
    
    async def check_global_limit(self) -> bool:
        """Check if the system is within its global rate limit.
        
        Returns:
            True if within limit, False otherwise
        """
        now = time.time()
        # Global limit could be higher than per-key limits
        global_limit = self.max_requests_per_minute * 5  # 5x the per-key limit as an example
        return self._check_limit(self.global_requests, global_limit, now)
    
    async def add_request(self, api_key: str, user_id: str, endpoint: str):
        """Record a new API request.
        
        Args:
            api_key: The API key making the request
            user_id: The ID of the user making the request
            endpoint: The API endpoint being called
        """
        now = time.time()
        
        # Add to all relevant deques
        self._add_request(self.requests_by_api_key[api_key], now)
        self._add_request(self.requests_by_user[user_id], now)
        self._add_request(self.requests_by_endpoint[endpoint], now)
        self._add_request(self.global_requests, now)
    
    async def is_allowed(self, api_key: str, user_id: str, endpoint: str) -> bool:
        """Check if a request is allowed based on all rate limits.
        
        Args:
            api_key: The API key making the request
            user_id: The ID of the user making the request
            endpoint: The API endpoint being called
            
        Returns:
            True if request is allowed, False otherwise
        """
        # Check all limits
        checks = [
            self.check_api_key_limit(api_key),
            self.check_user_limit(user_id),
            self.check_endpoint_limit(endpoint),
            self.check_global_limit()
        ]
        
        results = await asyncio.gather(*checks)
        
        return all(results)  # All checks must pass for the request to be allowed
    
    async def enforce_limit(self, api_key: str, user_id: str, endpoint: str):
        """Enforce rate limiting, raising an exception if limits are exceeded.
        
        Args:
            api_key: The API key making the request
            user_id: The ID of the user making the request
            endpoint: The API endpoint being called
            
        Raises:
            AILimitExceededException: If any rate limit is exceeded
        """
        if not await self.is_allowed(api_key, user_id, endpoint):
            raise AILimitExceededException(
                f"Rate limit exceeded for API key, user, or endpoint: {endpoint}"
            )
        
        # Record the request since it's allowed
        await self.add_request(api_key, user_id, endpoint)


class AIUsageTracker:
    """Track AI API usage for cost management and analytics."""
    
    def __init__(self):
        """Initialize the usage tracker."""
        self.usage_stats: Dict[str, Dict] = defaultdict(lambda: {
            "requests_count": 0,
            "tokens_used": 0,
            "cost_estimate": 0.0,
            "last_updated": time.time()
        })
        
        # Track by user
        self.user_usage: Dict[str, Dict] = defaultdict(lambda: {
            "requests_count": 0,
            "tokens_used": 0,
            "cost_estimate": 0.0,
            "last_updated": time.time()
        })
    
    async def record_usage(self, api_key: str, user_id: str, tokens_used: int = 0, cost_estimate: float = 0.0):
        """Record AI API usage.
        
        Args:
            api_key: The API key used for the request
            user_id: The ID of the user making the request
            tokens_used: Number of tokens used in the request
            cost_estimate: Estimated cost of the request
        """
        now = time.time()
        
        # Update API key stats
        self.usage_stats[api_key]["requests_count"] += 1
        self.usage_stats[api_key]["tokens_used"] += tokens_used
        self.usage_stats[api_key]["cost_estimate"] += cost_estimate
        self.usage_stats[api_key]["last_updated"] = now
        
        # Update user stats
        self.user_usage[user_id]["requests_count"] += 1
        self.user_usage[user_id]["tokens_used"] += tokens_used
        self.user_usage[user_id]["cost_estimate"] += cost_estimate
        self.user_usage[user_id]["last_updated"] = now
    
    def get_usage_stats(self, api_key: str) -> Optional[Dict]:
        """Get usage statistics for an API key.
        
        Args:
            api_key: The API key to get stats for
            
        Returns:
            Usage statistics or None if not found
        """
        if api_key in self.usage_stats:
            return self.usage_stats[api_key]
        return None
    
    def get_user_usage(self, user_id: str) -> Optional[Dict]:
        """Get usage statistics for a user.
        
        Args:
            user_id: The user ID to get stats for
            
        Returns:
            Usage statistics or None if not found
        """
        if user_id in self.user_usage:
            return self.user_usage[user_id]
        return None


# Global instances
ai_rate_limiter = AIRateLimiter()
ai_usage_tracker = AIUsageTracker()


# Decorator for easy rate limit enforcement
def rate_limit_ai_endpoint(endpoint_name: str):
    """Decorator to add rate limiting to AI endpoints.
    
    Args:
        endpoint_name: Name of the endpoint to track
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract API key and user ID from kwargs or request
            request = kwargs.get('request')
            if request:
                api_key = getattr(request.state, 'api_key', 'unknown')
                user_id = getattr(request.state, 'user_id', 'unknown')
            else:
                # Fallback if request isn't passed directly
                api_key = 'unknown'
                user_id = 'unknown'
            
            # Check rate limits
            try:
                await ai_rate_limiter.enforce_limit(api_key, user_id, endpoint_name)
            except AILimitExceededException:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded for AI API calls"
                )
            
            # Execute the original function
            result = await func(*args, **kwargs)
            
            # Potentially track usage here if tokens/costs are known
            # For now, we'll just record the request
            await ai_usage_tracker.record_usage(api_key, user_id)
            
            return result
        return wrapper
    return decorator