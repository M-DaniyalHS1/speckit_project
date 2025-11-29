"""Authentication schemas for AI-Enhanced Interactive Book Agent."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Token(BaseModel):
    """Schema for authentication tokens."""
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None


class TokenData(BaseModel):
    """Schema for token data payload."""
    username: Optional[str] = None
    user_id: Optional[str] = None
    email: Optional[str] = None


class UserCreate(BaseModel):
    """Schema for user registration data."""
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferences: Optional[dict] = {}

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "first_name": "John",
                "last_name": "Doe"
            }
        }


class UserLogin(BaseModel):
    """Schema for user login data."""
    email: str
    password: str

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }