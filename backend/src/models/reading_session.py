"""ReadingSession model for the AI-Enhanced Interactive Book Agent.

This module defines the ReadingSession data model with proper type hints and
validation using Pydantic for API request/response handling.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class ReadingSessionBase(BaseModel):
    """Base ReadingSession model with common fields for requests and responses."""
    user_id: str = Field(..., description="ID of the user associated with this session")
    book_id: str = Field(..., description="ID of the book being read in this session")

    class Config:
        """Pydantic configuration for the ReadingSession model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class ReadingSessionCreate(ReadingSessionBase):
    """Model for creating a new reading session with required fields."""
    current_position: Optional[int] = Field(0, ge=0, description="Current reading position (e.g., page number or character index)")
    current_chapter: Optional[str] = Field(None, max_length=100, description="Current chapter name or number")


class ReadingSessionUpdate(BaseModel):
    """Model for updating reading session information."""
    current_position: Optional[int] = Field(None, ge=0, description="Current reading position (e.g., page number or character index)")
    current_chapter: Optional[str] = Field(None, max_length=100, description="Current chapter name or number")
    last_read_at: Optional[datetime] = Field(None, description="When the user last read during this session")

    class Config:
        """Pydantic configuration for the ReadingSession model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class ReadingSessionInDB(ReadingSessionBase):
    """Model representing a reading session stored in the database with additional fields."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique session identifier")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="When the session was started")
    last_read_at: datetime = Field(default_factory=datetime.utcnow, description="When the user last read during this session")
    current_position: int = Field(0, ge=0, description="Current reading position (e.g., page number or character index)")
    current_chapter: Optional[str] = Field(None, max_length=100, description="Current chapter name or number")
    current_location: Optional[str] = Field("1:1:1", description="Current reading location (chapter:page:paragraph)")
    current_position_percent: Optional[int] = Field(0, ge=0, le=100, description="Current reading progress as percentage (0-100)")
    is_active: bool = Field(default=True, description="Whether this session is currently active")
    total_time_spent: int = Field(default=0, ge=0, description="Total time spent reading in this session (in seconds)")

    class Config:
        """Pydantic configuration for the ReadingSession model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class ReadingSession(ReadingSessionInDB):
    """Public ReadingSession model."""
    pass