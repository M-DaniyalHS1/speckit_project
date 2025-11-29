"""Response models for the AI-Enhanced Interactive Book Agent API.

This module defines standardized response models that provide consistent API responses
across all endpoints.
"""
from typing import Any, Optional, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime
from fastapi import status
from fastapi.responses import JSONResponse


class BaseResponse(BaseModel):
    """Base response model for all API responses."""
    success: bool = True
    message: str = "Success"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    status_code: int = status.HTTP_200_OK


class SuccessResponse(BaseResponse):
    """Standardized success response model."""
    data: Optional[Any] = None
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseResponse):
    """Standardized error response model."""
    error_code: str
    details: Optional[Dict[str, Any]] = None
    
    def to_json_response(self):
        """Convert this error response to a FastAPI JSONResponse."""
        return JSONResponse(
            content=self.model_dump(),
            status_code=self.status_code
        )


class ValidationErrorResponse(ErrorResponse):
    """Response for validation errors."""
    details: List[Dict[str, Any]]


class UnifiedErrorResponse(BaseResponse):
    """Unified error response model for all errors."""
    error_code: str
    details: Optional[Dict[str, Any]] = None
    success: bool = False  # Override to always be False for errors
    
    def to_json_response(self):
        """Convert this error response to a FastAPI JSONResponse."""
        return JSONResponse(
            content=self.model_dump(),
            status_code=self.status_code
        )


class PaginationInfo(BaseModel):
    """Pagination information model."""
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseResponse):
    """Response model for paginated data."""
    data: Any
    pagination: PaginationInfo


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    details: Optional[Dict[str, Any]] = None


class RateLimitResponse(BaseModel):
    """Response model for rate limiting information."""
    rate_limit_remaining: int
    rate_limit_reset: str
    rate_limit_total: int