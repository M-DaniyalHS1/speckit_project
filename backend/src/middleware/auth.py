"""Authentication middleware for the AI-Enhanced Interactive Book Agent.

This module implements middleware to handle authentication and authorization
for all API endpoints in the application.
"""
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from jose import JWTError, jwt
from backend.src.config import settings
from backend.src.auth.utils import verify_token


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware to handle JWT token verification for protected routes."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process the request and verify authentication token where required.
        
        Args:
            request: The incoming request object
            call_next: The next middleware or endpoint in the chain
            
        Returns:
            Response: The response object after processing the request
        """
        # Define paths that don't require authentication
        public_paths = [
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
        ]
        
        # Check if the path requires authentication
        requires_auth = not any(
            request.url.path.startswith(path) for path in public_paths
        )
        
        # Extract token only if the path requires authentication
        if requires_auth:
            authorization = request.headers.get("Authorization")
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
                
            except JWTError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        response = await call_next(request)
        return response