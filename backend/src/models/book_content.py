"""BookContent model for the AI-Enhanced Interactive Book Agent.

This module defines the BookContent data model with proper type hints and 
validation using Pydantic for API request/response handling.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


class BookContentBase(BaseModel):
    """Base BookContent model with common fields for requests and responses."""
    book_id: str = Field(..., description="ID of the book this content belongs to")
    content_type: str = Field(..., description="Type of content (e.g., 'chapter', 'section', 'paragraph')")
    content: str = Field(..., min_length=1, description="The actual content text")
    
    class Config:
        """Pydantic configuration for the BookContent model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class BookContentCreate(BookContentBase):
    """Model for creating new book content with required fields."""
    chunk_index: Optional[int] = Field(None, ge=0, description="Index of this content chunk within the book")
    parent_id: Optional[str] = Field(None, description="ID of the parent content (if this is a subsection)")
    metadata: Optional[dict] = Field(None, description="Additional metadata about this content")


class BookContentUpdate(BaseModel):
    """Model for updating book content information."""
    content: Optional[str] = Field(None, min_length=1, description="The actual content text")
    chunk_index: Optional[int] = Field(None, ge=0, description="Index of this content chunk within the book")
    metadata: Optional[dict] = Field(None, description="Additional metadata about this content")
    
    class Config:
        """Pydantic configuration for the BookContent model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class BookContentInDB(BookContentBase):
    """Model representing book content stored in the database with additional fields."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique content identifier")
    chunk_index: Optional[int] = Field(None, ge=0, description="Index of this content chunk within the book")
    parent_id: Optional[str] = Field(None, description="ID of the parent content (if this is a subsection)")
    page_number: Optional[int] = Field(None, ge=1, description="Page number where this content appears")
    section_title: Optional[str] = Field(None, max_length=200, description="Title of the section this content belongs to")
    vector_id: Optional[str] = Field(None, description="ID in the vector database for RAG functionality")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the content was added to the system")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the content was last updated")
    metadata: Optional[dict] = Field(None, description="Additional metadata about this content")
    
    class Config:
        """Pydantic configuration for the BookContent model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class BookContent(BookContentInDB):
    """Public BookContent model."""
    pass