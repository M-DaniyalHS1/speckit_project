"""API utilities for error handling, validation, and response formatting in the AI-Enhanced Interactive Book Agent.

This module provides standardized utilities for error handling, request validation,
and unified response formatting across all API endpoints.
"""
from typing import Union, Optional, Dict, Any, List
from enum import Enum
from fastapi import HTTPException, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging
from datetime import datetime

from backend.src.models.responses import (
    ErrorResponse, 
    ValidationErrorResponse, 
    SuccessResponse,
    UnifiedErrorResponse
)


class ErrorCode(str, Enum):
    """Standardized error codes for the API."""
    # Generic codes
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND_ERROR = "NOT_FOUND_ERROR"
    CONFLICT_ERROR = "CONFLICT_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Domain-specific codes
    BOOK_PROCESSING_ERROR = "BOOK_PROCESSING_ERROR"
    SEARCH_ERROR = "SEARCH_ERROR"
    EXPLANATION_GENERATION_ERROR = "EXPLANATION_GENERATION_ERROR"
    SUMMARIZATION_ERROR = "SUMMARIZATION_ERROR"
    SESSION_ERROR = "SESSION_ERROR"


class APIErrorHandler:
    """Utility class for handling various types of API errors consistently."""

    @staticmethod
    def handle_validation_error(exc: RequestValidationError) -> ValidationErrorResponse:
        """Handle request validation errors.

        Args:
            exc: The RequestValidationError instance

        Returns:
            Standardized ValidationErrorResponse
        """
        errors = []
        for error in exc.errors():
            errors.append({
                "loc": error["loc"],
                "type": error["type"],
                "msg": error["msg"],
                "input": error.get("input", None),
            })

        error_response = ValidationErrorResponse(
            error_code=ErrorCode.VALIDATION_ERROR.value,
            message="Validation failed for request parameters",
            details=errors,
            timestamp=datetime.utcnow().isoformat()
        )
        return error_response

    @staticmethod
    def handle_pydantic_validation_error(exc: ValidationError) -> ValidationErrorResponse:
        """Handle Pydantic validation errors.

        Args:
            exc: The ValidationError instance

        Returns:
            Standardized ValidationErrorResponse
        """
        errors = []
        for error in exc.errors():
            errors.append({
                "loc": error["loc"],
                "type": error["type"],
                "msg": error["msg"],
                "input": error.get("input", None),
            })

        error_response = ValidationErrorResponse(
            error_code=ErrorCode.VALIDATION_ERROR.value,
            message="Validation failed for data model",
            details=errors,
            timestamp=datetime.utcnow().isoformat()
        )
        return error_response

    @staticmethod
    def handle_database_error(exc: SQLAlchemyError) -> ErrorResponse:
        """Handle database-related errors.

        Args:
            exc: The SQLAlchemyError instance

        Returns:
            Standardized ErrorResponse
        """
        error_msg = str(exc.orig) if hasattr(exc, 'orig') and exc.orig else str(exc)
        
        # Determine specific error type based on the exception
        if isinstance(exc, IntegrityError):
            error_code = ErrorCode.CONFLICT_ERROR
            message = f"Database integrity constraint violation: {error_msg}"
        else:
            error_code = ErrorCode.UNKNOWN_ERROR
            message = f"Database error occurred: {error_msg}"

        error_response = ErrorResponse(
            error_code=error_code.value,
            message=message,
            details={"original_error": error_msg},
            timestamp=datetime.utcnow().isoformat()
        )
        return error_response

    @staticmethod
    def handle_http_error(status_code: int, detail: Union[str, Dict[str, Any]]) -> Union[ErrorResponse, ValidationErrorResponse]:
        """Handle HTTP errors and convert to standardized responses.

        Args:
            status_code: HTTP status code
            detail: Error detail information

        Returns:
            Standardized error response
        """
        if status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
            error_code = ErrorCode.VALIDATION_ERROR
            message = "Unprocessable entity - validation failed"
        elif status_code == status.HTTP_401_UNAUTHORIZED:
            error_code = ErrorCode.AUTHENTICATION_ERROR
            message = "Authentication required"
        elif status_code == status.HTTP_403_FORBIDDEN:
            error_code = ErrorCode.AUTHORIZATION_ERROR
            message = "Access forbidden"
        elif status_code == status.HTTP_404_NOT_FOUND:
            error_code = ErrorCode.NOT_FOUND_ERROR
            message = "Resource not found"
        elif status_code == status.HTTP_409_CONFLICT:
            error_code = ErrorCode.CONFLICT_ERROR
            message = "Resource conflict"
        elif status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            error_code = ErrorCode.RATE_LIMIT_EXCEEDED
            message = "Rate limit exceeded"
        else:
            error_code = ErrorCode.UNKNOWN_ERROR
            message = f"HTTP error {status_code} occurred"

        error_response = ErrorResponse(
            error_code=error_code.value,
            message=message,
            details={"status_code": status_code, "detail": detail},
            timestamp=datetime.utcnow().isoformat()
        )
        return error_response

    @staticmethod
    def create_error_response(
        error_code: ErrorCode, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ) -> ErrorResponse:
        """Create a standardized error response.

        Args:
            error_code: Standardized error code
            message: Human-readable error message
            details: Additional error details
            status_code: HTTP status code

        Returns:
            Standardized ErrorResponse instance
        """
        return ErrorResponse(
            error_code=error_code.value,
            message=message,
            details=details or {},
            timestamp=datetime.utcnow().isoformat()
        )


class APIValidator:
    """Utility class for request validation and data sanitization."""

    @staticmethod
    def validate_book_content(content: str, max_length: int = 1000000) -> bool:
        """Validate book content for length and format.

        Args:
            content: Content to validate
            max_length: Maximum allowed content length

        Returns:
            True if valid, raises ValidationError otherwise
        """
        if len(content) > max_length:
            raise ValidationError([
                {
                    "loc": ("content",),
                    "msg": f"Content exceeds maximum length of {max_length} characters",
                    "type": "value_error.length"
                }
            ])

        # Additional checks can be added here
        # For example: check for malicious code, ensure proper encoding, etc.
        return True

    @staticmethod
    def validate_user_input(user_input: str, max_length: int = 1000) -> str:
        """Sanitize and validate user input.

        Args:
            user_input: Input to validate
            max_length: Maximum allowed length

        Returns:
            Sanitized input string
        """
        if len(user_input) > max_length:
            raise ValidationError([
                {
                    "loc": ("input",),
                    "msg": f"Input exceeds maximum length of {max_length} characters",
                    "type": "value_error.length"
                }
            ])

        # Basic sanitization - remove potentially dangerous characters
        # This is a simple example; a more robust sanitization would be needed for production
        sanitized = user_input.strip()

        return sanitized

    @staticmethod
    def validate_search_query(query: str, min_length: int = 1, max_length: int = 500) -> bool:
        """Validate a search query.

        Args:
            query: Query string to validate
            min_length: Minimum allowed query length
            max_length: Maximum allowed query length

        Returns:
            True if valid, raises ValidationError otherwise
        """
        if len(query) < min_length:
            raise ValidationError([
                {
                    "loc": ("query",),
                    "msg": f"Query is too short, minimum length is {min_length} characters",
                    "type": "value_error.length"
                }
            ])

        if len(query) > max_length:
            raise ValidationError([
                {
                    "loc": ("query",),
                    "msg": f"Query exceeds maximum length of {max_length} characters",
                    "type": "value_error.length"
                }
            ])

        # Additional validation can be added here
        # For example: check for potentially harmful patterns
        return True


class APIResponseFormatter:
    """Utility class for formatting API responses consistently."""

    @staticmethod
    def success_response(
        message: str = "Operation successful",
        data: Optional[Any] = None,
        status_code: int = status.HTTP_200_OK
    ) -> SuccessResponse:
        """Create a standardized success response.

        Args:
            message: Success message
            data: Optional response data
            status_code: HTTP status code

        Returns:
            Standardized SuccessResponse
        """
        return SuccessResponse(
            success=True,
            message=message,
            data=data,
            status_code=status_code,
            timestamp=datetime.utcnow().isoformat()
        )

    @staticmethod
    def paginated_response(
        items: List[Any],
        page: int,
        page_size: int,
        total_items: int,
        message: str = "Paginated results"
    ) -> Dict[str, Any]:
        """Create a standardized paginated response.

        Args:
            items: List of items in the current page
            page: Current page number
            page_size: Number of items per page
            total_items: Total number of items available
            message: Response message

        Returns:
            Dictionary with pagination information
        """
        total_pages = (total_items + page_size - 1) // page_size  # Ceiling division

        return {
            "success": True,
            "message": message,
            "data": {
                "items": items,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            },
            "status_code": status.HTTP_200_OK,
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    def unified_error_response(
        message: str,
        error_code: str,
        status_code: int,
        details: Optional[Dict[str, Any]] = None
    ) -> UnifiedErrorResponse:
        """Create a unified error response following all API standards.

        Args:
            message: Error message
            error_code: Standardized error code
            status_code: HTTP status code
            details: Additional error details

        Returns:
            UnifiedErrorResponse instance
        """
        return UnifiedErrorResponse(
            success=False,
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details or {},
            timestamp=datetime.utcnow().isoformat()
        )


def setup_exception_handlers(app):
    """Set up global exception handlers for the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        """Handle request validation errors globally."""
        from backend.src.utils.logging import logger_manager
        logger_manager.log_validation_error(
            logging.getLogger(__name__),
            f"Validation error for request {request.url}",
            exc
        )
        
        error_response = APIErrorHandler.handle_validation_error(exc)
        return error_response.to_json_response()

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request, exc):
        """Handle Pydantic validation errors globally."""
        from backend.src.utils.logging import logger_manager
        logger_manager.log_validation_error(
            logging.getLogger(__name__),
            f"Pydantic validation error for request {request.url}",
            exc
        )
        
        error_response = APIErrorHandler.handle_pydantic_validation_error(exc)
        return error_response.to_json_response()

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        """Handle HTTP exceptions globally."""
        from backend.src.utils.logging import logger_manager
        logger_manager.log_http_error(
            logging.getLogger(__name__),
            f"HTTP error {exc.status_code} for request {request.url}",
            exc
        )
        
        error_response = APIErrorHandler.handle_http_error(exc.status_code, exc.detail)
        return error_response.to_json_response()

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request, exc):
        """Handle database integrity errors globally."""
        from backend.src.utils.logging import logger_manager
        logger_manager.log_database_error(
            logging.getLogger(__name__),
            f"Database integrity error for request {request.url}",
            exc
        )
        
        error_response = APIErrorHandler.handle_database_error(exc)
        return error_response.to_json_response()

    @app.exception_handler(SQLAlchemyError)
    async def database_error_handler(request, exc):
        """Handle database errors globally."""
        from backend.src.utils.logging import logger_manager
        logger_manager.log_database_error(
            logging.getLogger(__name__),
            f"Database error for request {request.url}",
            exc
        )
        
        error_response = APIErrorHandler.handle_database_error(exc)
        return error_response.to_json_response()

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        """Handle all other unhandled exceptions globally."""
        from backend.src.utils.logging import logger_manager
        logger_manager.log_error(
            logging.getLogger(__name__),
            f"Unhandled error for request {request.url}",
            exc
        )
        
        error_response = APIErrorHandler.create_error_response(
            error_code=ErrorCode.UNKNOWN_ERROR,
            message=f"An unexpected error occurred: {str(exc)}",
            details={"type": type(exc).__name__, "request_path": str(request.url)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        return error_response.to_json_response()


# Initialize the standard response classes if they don't exist
def init_standard_responses():
    """Initialize standard response classes with JSON response methods."""
    
    def to_json_response(self):
        """Convert the response model to a FastAPI JSONResponse."""
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=self.model_dump(),
            status_code=getattr(self, 'status_code', 200)
        )
    
    # Add convenience method to all response models
    if not hasattr(ErrorResponse, 'to_json_response'):
        ErrorResponse.to_json_response = to_json_response
    if not hasattr(ValidationErrorResponse, 'to_json_response'):
        ValidationErrorResponse.to_json_response = to_json_response
    if not hasattr(SuccessResponse, 'to_json_response'):
        SuccessResponse.to_json_response = to_json_response
    if not hasattr(UnifiedErrorResponse, 'to_json_response'):
        UnifiedErrorResponse.to_json_response = to_json_response


# Initialize standard responses when module is loaded
init_standard_responses()