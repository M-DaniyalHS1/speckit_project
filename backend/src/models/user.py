"""User model for the AI-Enhanced Interactive Book Agent.

This module defines the User data model with proper type hints and 
validation using Pydantic for API request/response handling.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
import uuid


class UserBase(BaseModel):
    """Base User model with common fields for requests and responses."""
    email: EmailStr = Field(..., description="User's email address")
    first_name: str = Field(..., min_length=1, max_length=50, description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=50, description="User's last name")
    
    class Config:
        """Pydantic configuration for the User model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class UserCreate(UserBase):
    """Model for creating a new user with required fields."""
    password: str = Field(..., min_length=8, description="User's password")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password meets security requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        # Additional password validation could go here
        return v


class UserUpdate(BaseModel):
    """Model for updating user information."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="User's first name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="User's last name")
    
    class Config:
        """Pydantic configuration for the User model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class UserInDB(UserBase):
    """Model representing a user stored in the database with additional fields."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique user identifier")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    is_verified: bool = Field(default=False, description="Whether the user has verified their email")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the user account was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the user account was last updated")
    
    class Config:
        """Pydantic configuration for the User model."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy compatibility


class User(UserInDB):
    """Public User model that excludes sensitive information."""
    # This model is meant to be returned to clients, 
    # without sensitive information like password hash
    pass