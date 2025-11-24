"""Explanation model for the AI-Enhanced Interactive Book Agent.

This module defines the Explanation data model with proper type hints and 
validation using Pydantic for API request/response handling.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


class ExplanationBase(BaseModel):
    """Base Explanation model with common fields for requests and responses."""
    query_id: str = Field(..., description="ID of the query that generated this explanation")
    book_id: str = Field(..., description="ID of the book this explanation is about")
    content: str = Field(..., min_length=1, description="The explanation text")
    
    class Config:
        """Pydantic configuration for the Explanation model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class ExplanationCreate(ExplanationBase):
    """Model for creating a new explanation with required fields."""
    explanation_type: str = Field(default="detailed", description="Type of explanation ('simple', 'detailed', etc.)")
    source_content_ids: Optional[List[str]] = Field(None, description="IDs of content that were used as sources")
    complexity_level: Optional[str] = Field("medium", description="Complexity level of the explanation")


class ExplanationUpdate(BaseModel):
    """Model for updating explanation information."""
    content: Optional[str] = Field(None, min_length=1, description="The explanation text")
    
    class Config:
        """Pydantic configuration for the Explanation model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class ExplanationInDB(ExplanationBase):
    """Model representing an explanation stored in the database with additional fields."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique explanation identifier")
    explanation_type: str = Field(default="detailed", description="Type of explanation ('simple', 'detailed', etc.)")
    source_content_ids: Optional[List[str]] = Field(None, description="IDs of content that were used as sources")
    complexity_level: str = Field(default="medium", description="Complexity level of the explanation")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the explanation was generated")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the explanation was last updated")
    
    class Config:
        """Pydantic configuration for the Explanation model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class Explanation(ExplanationInDB):
    """Public Explanation model."""
    pass