"""Authentication middleware for the AI-Enhanced Interactive Book Agent.

This module implements middleware to handle authentication and authorization
for all API endpoints in the application.
"""
import re
from typing import Optional, Set
from fastapi import Request, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from jose import JWTError
from backend.src.config import settings
from backend.src.auth.utils import verify_token


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware to handle JWT token verification for protected routes."""

    def __init__(self, app, public_paths: Optional[Set[str]] = None, public_path_patterns: Optional[Set[str]] = None):
        """Initialize the authentication middleware.

        Args:
            app: The FastAPI application instance
            public_paths: Set of exact paths that don't require authentication
            public_path_patterns: Set of regex patterns for paths that don't require authentication
        """
        super().__init__(app)
        self.public_paths = public_paths or {
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health"
        }

        # Default public path patterns (regex)
        self.public_path_patterns = public_path_patterns or {
            r"/api/v1/auth/.*",  # All auth endpoints
        }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process the request and verify authentication token where required.

        Args:
            request: The incoming request object
            call_next: The next middleware or endpoint in the chain

        Returns:
            Response: The response object after processing the request
        """
        # Check if path is public (doesn't require auth)
        is_public_path = (
            request.url.path in self.public_paths or
            any(re.match(pattern, request.url.path) for pattern in self.public_path_patterns)
        )

        # Extract token only if the path requires authentication
        if not is_public_path:
            authorization = request.headers.get("Authorization")
            if not authorization:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            scheme, param = get_authorization_scheme_param(authorization)

            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            token = param

            try:
                # Verify the token using the utility function
                payload = verify_token(token)

                # Add user info to request state for use in endpoints
                request.state.user_id = payload.get("sub")
                request.state.user_role = payload.get("role", "user")
                request.state.token_payload = payload  # Store full payload for potential future use

            except JWTError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        response = await call_next(request)

        # Add security headers to response
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response