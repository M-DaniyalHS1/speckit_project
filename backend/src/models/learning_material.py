"""LearningMaterial model for the AI-Enhanced Interactive Book Agent.

This module defines the LearningMaterial data model with proper type hints and 
validation using Pydantic for API request/response handling.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class LearningMaterialBase(BaseModel):
    """Base LearningMaterial model with common fields for requests and responses."""
    user_id: str = Field(..., description="ID of the user this learning material belongs to")
    book_id: str = Field(..., description="ID of the book this learning material is based on")
    title: str = Field(..., min_length=1, max_length=200, description="Title of the learning material")
    material_type: str = Field(..., description="Type of learning material (e.g., 'quiz', 'flashcard', 'note', 'summary')")
    
    class Config:
        """Pydantic configuration for the LearningMaterial model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class LearningMaterialCreate(LearningMaterialBase):
    """Model for creating new learning material with required fields."""
    content: Optional[str] = Field(None, description="The content of the learning material")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the learning material")


class LearningMaterialUpdate(BaseModel):
    """Model for updating learning material information."""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Title of the learning material")
    content: Optional[str] = Field(None, description="The content of the learning material")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the learning material")
    
    class Config:
        """Pydantic configuration for the LearningMaterial model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class LearningMaterialInDB(LearningMaterialBase):
    """Model representing learning material stored in the database with additional fields."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique learning material identifier")
    content: Optional[str] = Field(None, description="The content of the learning material")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the learning material was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the learning material was last updated")
    is_active: bool = Field(default=True, description="Whether this learning material is active")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the learning material")
    
    class Config:
        """Pydantic configuration for the LearningMaterial model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class LearningMaterial(LearningMaterialInDB):
    """Public LearningMaterial model."""
    pass