"""API documentation with OpenAPI/Swagger for the AI-Enhanced Interactive Book Agent.

This module configures and provides API documentation using FastAPI's built-in 
OpenAPI and Swagger UI capabilities.
"""
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from typing import Dict, Any


def configure_api_docs(app: FastAPI) -> None:
    """
    Configure API documentation for the application.
    
    This function sets up both Swagger UI and ReDoc documentation interfaces
    with custom configuration and branding.
    
    Args:
        app: The FastAPI application instance
    """
    # Custom OpenAPI configuration
    app.openapi_schema = get_custom_openapi_schema(app)


def get_custom_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """
    Generate a custom OpenAPI schema with enhanced documentation.
    
    Args:
        app: The FastAPI application instance
        
    Returns:
        Dictionary representing the OpenAPI schema
    """
    if app.openapi_schema:
        return app.openapi_schema

    # Generate the basic OpenAPI schema
    openapi_schema = get_openapi(
        title="AI-Enhanced Interactive Book Agent API",
        version="1.0.0",
        description="""
# AI-Enhanced Interactive Book Agent API Documentation

Welcome to the API documentation for the AI-Enhanced Interactive Book Agent!

## Overview
This API provides intelligent reading assistance, including:
- Personalized reading session management
- Semantic content search and retrieval
- AI-powered explanations and teaching
- Content summarization and note-taking
- Learning tools and tutoring assistance

## Authentication
Most endpoints require authentication. Include your JWT token in the Authorization header:
`Authorization: Bearer YOUR_JWT_TOKEN`

## Status Codes
- `200`: Success
- `400`: Bad Request (validation error)
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Resource not found
- `429`: Rate limited
- `500`: Internal server error

## Rate Limiting
API calls are rate-limited to prevent abuse. Exceeding limits will result in 429 responses.

## Need Help?
If you have questions about using this API, please contact the development team.
        """,
        routes=app.routes,
    )

    # Add custom server information
    openapi_schema["servers"] = [
        {
            "url": "https://api.book-agent.example.com",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.book-agent.example.com",
            "description": "Staging server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ]

    # Add custom tags with descriptions and external documentation
    openapi_schema["tags"] = [
        {
            "name": "Authentication",
            "description": "Endpoints for user authentication and token management",
            "externalDocs": {
                "description": "Find more about authentication flow",
                "url": "https://docs.book-agent.example.com/auth"
            }
        },
        {
            "name": "Books",
            "description": "Manage books and their content",
            "externalDocs": {
                "description": "Find more about book formats supported",
                "url": "https://docs.book-agent.example.com/books"
            }
        },
        {
            "name": "Sessions",
            "description": "Reading session management and progress tracking",
            "externalDocs": {
                "description": "Learn about session lifecycle",
                "url": "https://docs.book-agent.example.com/sessions"
            }
        },
        {
            "name": "Search",
            "description": "Semantic search functionality for book content",
            "externalDocs": {
                "description": "Understanding semantic search",
                "url": "https://docs.book-agent.example.com/search"
            }
        },
        {
            "name": "Explanations",
            "description": "AI-powered content explanations and teaching",
            "externalDocs": {
                "description": "Learn about explanation customization",
                "url": "https://docs.book-agent.example.com/explanations"
            }
        },
        {
            "name": "Summaries",
            "description": "Content summarization and note-taking features",
            "externalDocs": {
                "description": "Learn about summarization techniques",
                "url": "https://docs.book-agent.example.com/summaries"
            }
        },
        {
            "name": "Learning Tools",
            "description": "Quiz generation, flashcards, and tutoring assistance",
            "externalDocs": {
                "description": "Understanding learning tools API",
                "url": "https://docs.book-agent.example.com/learning-tools"
            }
        }
    ]

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token in the format: Bearer <token>"
        }
    }

    # Apply security globally (can be overridden on specific endpoints)
    openapi_schema["security"] = [{"BearerAuth": []}]

    return openapi_schema


def add_documentation_routes(app: FastAPI) -> None:
    """
    Add custom documentation routes to the application.
    
    This adds both Swagger UI and ReDoc documentation interfaces with custom configurations.
    
    Args:
        app: The FastAPI application instance
    """
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """Custom Swagger UI with enhanced configuration."""
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@latest/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@latest/swagger-ui.css",
            swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        )

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        """Custom ReDoc UI with enhanced configuration."""
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=app.title + " - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js",
            redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        )

    @app.get("/openapi.json", include_in_schema=False)
    async def get_open_api_endpoint():
        """Serve the OpenAPI schema as JSON."""
        return get_custom_openapi_schema(app)


def setup_api_documentation(app: FastAPI) -> None:
    """
    Complete setup for API documentation.
    
    This function orchestrates the complete setup of API documentation
    including schema configuration and documentation routes.
    
    Args:
        app: The FastAPI application instance
    """
    # Configure the API schema
    configure_api_docs(app)
    
    # Add documentation routes
    add_documentation_routes(app)


# Example usage as a standalone module
if __name__ == "__main__":
    # This would typically be called from the main application setup
    example_app = FastAPI(
        title="AI-Enhanced Interactive Book Agent API",
        version="1.0.0",
        description="API for the Book Agent application",
        docs_url=None,  # Disable default docs
        redoc_url=None,  # Disable default redoc
    )
    
    # Setup documentation
    setup_api_documentation(example_app)
    
    # Add a simple test endpoint
    @example_app.get("/")
    def read_root():
        return {"message": "Welcome to the AI-Enhanced Interactive Book Agent API"}
    
    print("API Documentation setup complete!")
    print("Swagger UI available at: /docs")
    print("ReDoc available at: /redoc")
    print("OpenAPI JSON available at: /openapi.json")