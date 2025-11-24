"""Query model for the AI-Enhanced Interactive Book Agent.

This module defines the Query data model with proper type hints and 
validation using Pydantic for API request/response handling.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class QueryBase(BaseModel):
    """Base Query model with common fields for requests and responses."""
    user_id: str = Field(..., description="ID of the user who made the query")
    book_id: str = Field(..., description="ID of the book the query is about")
    query_text: str = Field(..., min_length=1, max_length=1000, description="The actual query text")
    
    class Config:
        """Pydantic configuration for the Query model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class QueryCreate(QueryBase):
    """Model for creating a new query with required fields."""
    query_type: str = Field(default="general", description="Type of query (e.g., 'search', 'explanation', 'summary')")
    context: Optional[str] = Field(None, description="Additional context for the query")


class QueryUpdate(BaseModel):
    """Model for updating query information."""
    query_text: Optional[str] = Field(None, min_length=1, max_length=1000, description="The actual query text")
    
    class Config:
        """Pydantic configuration for the Query model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class QueryInDB(QueryBase):
    """Model representing a query stored in the database with additional fields."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique query identifier")
    query_type: str = Field(default="general", description="Type of query (e.g., 'search', 'explanation', 'summary')")
    context: Optional[str] = Field(None, description="Additional context for the query")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the query was made")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the query was last updated")
    
    class Config:
        """Pydantic configuration for the Query model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class Query(QueryInDB):
    """Public Query model."""
    pass