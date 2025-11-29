"""Unit tests for the User model in the AI-Enhanced Interactive Book Agent.

This module contains comprehensive unit tests for all User model components,
including validation, creation, and field constraints.
"""
import pytest
from datetime import datetime
from backend.src.models.user import UserCreate, UserUpdate, UserInDB, User


def test_user_create_valid():
    """Test creating a valid UserCreate instance."""
    user_data = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password": "securepassword123"
    }
    
    user = UserCreate(**user_data)
    
    assert user.email == "test@example.com"
    assert user.first_name == "John"
    assert user.last_name == "Doe"
    assert user.password == "securepassword123"


def test_user_create_invalid_email():
    """Test that UserCreate rejects invalid email addresses."""
    user_data = {
        "email": "invalid-email",
        "first_name": "John",
        "last_name": "Doe",
        "password": "securepassword123"
    }
    
    with pytest.raises(ValueError):
        UserCreate(**user_data)


def test_user_create_short_password():
    """Test that UserCreate rejects passwords shorter than 8 characters."""
    user_data = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password": "short"
    }
    
    with pytest.raises(ValueError):
        UserCreate(**user_data)


def test_user_create_missing_required_fields():
    """Test that UserCreate rejects missing required fields."""
    # Missing email
    user_data = {
        "first_name": "John",
        "last_name": "Doe",
        "password": "securepassword123"
    }
    
    with pytest.raises(ValueError):
        UserCreate(**user_data)
    
    # Missing first_name
    user_data = {
        "email": "test@example.com",
        "last_name": "Doe",
        "password": "securepassword123"
    }
    
    with pytest.raises(ValueError):
        UserCreate(**user_data)
    
    # Missing last_name
    user_data = {
        "email": "test@example.com",
        "first_name": "John",
        "password": "securepassword123"
    }
    
    with pytest.raises(ValueError):
        UserCreate(**user_data)
    
    # Missing password
    user_data = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }
    
    with pytest.raises(ValueError):
        UserCreate(**user_data)


def test_user_update_partial():
    """Test updating only some fields with UserUpdate."""
    user_update = UserUpdate(first_name="Jane")
    
    assert user_update.first_name == "Jane"
    assert user_update.last_name is None


def test_user_indb_defaults():
    """Test that UserInDB has proper defaults."""
    user_data = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }
    
    user = UserInDB(**user_data)
    
    assert user.email == "test@example.com"
    assert user.first_name == "John"
    assert user.last_name == "Doe"
    assert user.id is not None  # UUID should be generated
    assert user.is_active is True
    assert user.is_verified is False
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)


def test_user_model():
    """Test the public User model."""
    user_data = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }
    
    user = User(**user_data)
    
    assert user.email == "test@example.com"
    assert user.first_name == "John"
    assert user.last_name == "Doe"
    assert user.id is not None  # UUID should be generated
    assert user.is_active is True
    assert user.is_verified is False
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)


def test_user_create_minimal_fields():
    """Test creating a UserCreate with minimal required fields."""
    user_data = {
        "email": "minimal@example.com",
        "first_name": "Min",
        "last_name": "Imal",
        "password": "asecurepassword"
    }
    
    user = UserCreate(**user_data)
    
    assert user.email == "minimal@example.com"
    assert user.first_name == "Min"
    assert user.last_name == "Imal"
    assert user.password == "asecurepassword"


def test_user_first_name_length_constraints():
    """Test first_name length constraints."""
    # Test with a very long first name (should fail)
    user_data = {
        "email": "test@example.com",
        "first_name": "A" * 51,  # More than 50 characters
        "last_name": "Doe",
        "password": "securepassword123"
    }
    
    with pytest.raises(ValueError):
        UserCreate(**user_data)
    
    # Test with empty first name (should fail)
    user_data = {
        "email": "test@example.com",
        "first_name": "",
        "last_name": "Doe",
        "password": "securepassword123"
    }
    
    with pytest.raises(ValueError):
        UserCreate(**user_data)


def test_user_last_name_length_constraints():
    """Test last_name length constraints."""
    # Test with a very long last name (should fail)
    user_data = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "A" * 51,  # More than 50 characters
        "password": "securepassword123"
    }

    with pytest.raises(ValueError):
        UserCreate(**user_data)

    # Test with empty last name (should fail)
    user_data = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "",
        "password": "securepassword123"
    }

    with pytest.raises(ValueError):
        UserCreate(**user_data)


def test_user_password_validation():
    """Test password validation with valid password."""
    user_data = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password": "securepassword123"  # Valid password
    }

    user = UserCreate(**user_data)
    assert user.password == "securepassword123"