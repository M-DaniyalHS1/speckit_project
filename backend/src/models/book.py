"""Book model for the AI-Enhanced Interactive Book Agent.

This module defines the Book data model with proper type hints and 
validation using Pydantic for API request/response handling.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


class BookBase(BaseModel):
    """Base Book model with common fields for requests and responses."""
    title: str = Field(..., min_length=1, max_length=200, description="Title of the book")
    author: str = Field(..., min_length=1, max_length=100, description="Author of the book")
    description: Optional[str] = Field(None, max_length=1000, description="Description of the book")
    isbn: Optional[str] = Field(None, max_length=13, description="ISBN of the book")
    
    class Config:
        """Pydantic configuration for the Book model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class BookCreate(BookBase):
    """Model for creating a new book with required fields."""
    content: Optional[str] = Field(None, description="Raw content of the book (for processing)")
    file_path: Optional[str] = Field(None, description="Path to the book file")


class BookUpdate(BaseModel):
    """Model for updating book information."""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Title of the book")
    author: Optional[str] = Field(None, min_length=1, max_length=100, description="Author of the book")
    description: Optional[str] = Field(None, max_length=1000, description="Description of the book")
    
    class Config:
        """Pydantic configuration for the Book model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class BookInDB(BookBase):
    """Model representing a book stored in the database with additional fields."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique book identifier")
    user_id: str = Field(..., description="ID of the user who owns this book")
    file_type: Optional[str] = Field(None, description="File type of the book (PDF, EPUB, etc.)")
    page_count: Optional[int] = Field(None, ge=1, description="Number of pages in the book")
    word_count: Optional[int] = Field(None, ge=0, description="Number of words in the book")
    is_processed: bool = Field(default=False, description="Whether the book content has been processed for RAG")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the book was added to the system")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the book was last updated")
    
    class Config:
        """Pydantic configuration for the Book model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class Book(BookInDB):
    """Public Book model."""
    pass