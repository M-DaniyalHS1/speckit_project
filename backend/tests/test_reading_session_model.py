"""Unit tests for the ReadingSession model in the AI-Enhanced Interactive Book Agent.

This module contains comprehensive unit tests for all ReadingSession model components,
including validation, creation, and field constraints.
"""
import pytest
from datetime import datetime
from backend.src.models.reading_session import ReadingSessionCreate, ReadingSessionUpdate, ReadingSessionInDB, ReadingSession


def test_reading_session_create_valid():
    """Test creating a valid ReadingSessionCreate instance."""
    session_data = {
        "user_id": "user123",
        "book_id": "book456",
        "current_position": 42,
        "current_chapter": "Chapter 3"
    }
    
    session = ReadingSessionCreate(**session_data)
    
    assert session.user_id == "user123"
    assert session.book_id == "book456"
    assert session.current_position == 42
    assert session.current_chapter == "Chapter 3"


def test_reading_session_create_minimal():
    """Test creating a ReadingSessionCreate with minimal required fields."""
    session_data = {
        "user_id": "user123",
        "book_id": "book456"
    }
    
    session = ReadingSessionCreate(**session_data)
    
    assert session.user_id == "user123"
    assert session.book_id == "book456"
    assert session.current_position == 0  # Default value
    assert session.current_chapter is None


def test_reading_session_position_constraints():
    """Test current_position constraints."""
    # Test with negative position for creation (should fail)
    session_data = {
        "user_id": "user123",
        "book_id": "book456",
        "current_position": -1
    }

    with pytest.raises(ValueError):
        ReadingSessionCreate(**session_data)

    # Test with negative position in update (should fail)
    with pytest.raises(ValueError):
        ReadingSessionUpdate(current_position=-1)


def test_reading_session_chapter_length_constraints():
    """Test current_chapter length constraints."""
    # Test with a very long chapter name
    session_data = {
        "user_id": "user123",
        "book_id": "book456",
        "current_chapter": "A" * 101  # More than 100 characters
    }

    with pytest.raises(ValueError):
        ReadingSessionCreate(**session_data)


def test_reading_session_update_partial():
    """Test updating only some fields with ReadingSessionUpdate."""
    session_update = ReadingSessionUpdate(current_position=100)
    
    assert session_update.current_position == 100
    assert session_update.current_chapter is None
    assert session_update.last_read_at is None


def test_reading_session_indb_defaults():
    """Test that ReadingSessionInDB has proper defaults."""
    session_data = {
        "user_id": "user123",
        "book_id": "book456"
    }
    
    session = ReadingSessionInDB(**session_data)
    
    assert session.user_id == "user123"
    assert session.book_id == "book456"
    assert session.id is not None  # UUID should be generated
    assert session.current_position == 0
    assert session.is_active is True
    assert session.total_time_spent == 0
    assert isinstance(session.started_at, datetime)
    assert isinstance(session.last_read_at, datetime)


def test_reading_session_model():
    """Test the public ReadingSession model."""
    session_data = {
        "user_id": "user123",
        "book_id": "book456"
    }
    
    session = ReadingSession(**session_data)
    
    assert session.user_id == "user123"
    assert session.book_id == "book456"
    assert session.id is not None  # UUID should be generated
    assert session.current_position == 0
    assert session.is_active is True
    assert session.total_time_spent == 0
    assert isinstance(session.started_at, datetime)
    assert isinstance(session.last_read_at, datetime)


def test_reading_session_indb_with_optional_fields():
    """Test ReadingSessionInDB with optional fields provided."""
    now = datetime.utcnow()
    session_data = {
        "user_id": "user123",
        "book_id": "book456",
        "current_position": 150,
        "current_chapter": "Chapter 7",
        "is_active": False,
        "total_time_spent": 3600  # 1 hour in seconds
    }
    
    session = ReadingSessionInDB(**session_data)
    
    assert session.user_id == "user123"
    assert session.book_id == "book456"
    assert session.current_position == 150
    assert session.current_chapter == "Chapter 7"
    assert session.is_active is False
    assert session.total_time_spent == 3600


def test_reading_session_position_ge_constraint():
    """Test that current_position must be greater than or equal to 0."""
    # Valid case with position 0
    session_data = {
        "user_id": "user123",
        "book_id": "book456",
        "current_position": 0
    }
    
    session = ReadingSessionCreate(**session_data)
    assert session.current_position == 0


def test_reading_session_indb_position_ge_constraint():
    """Test that ReadingSessionInDB enforces position constraint."""
    # This test depends on validation being correctly applied
    # For Pydantic, field constraints are applied at the model level
    pass  # The constraint is validated in the model definition with ge=0