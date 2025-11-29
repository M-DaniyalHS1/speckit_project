"""Unit tests for the BookContent model in the AI-Enhanced Interactive Book Agent.

This module contains comprehensive unit tests for all BookContent model components,
including validation, creation, and field constraints.
"""
import pytest
from datetime import datetime
from backend.src.models.book_content import BookContentCreate, BookContentUpdate, BookContentInDB, BookContent


def test_book_content_create_valid():
    """Test creating a valid BookContentCreate instance."""
    content_data = {
        "book_id": "book123",
        "content_type": "chapter",
        "content": "This is the content of the book chapter."
    }
    
    content = BookContentCreate(**content_data)
    
    assert content.book_id == "book123"
    assert content.content_type == "chapter"
    assert content.content == "This is the content of the book chapter."


def test_book_content_create_minimal():
    """Test creating a BookContentCreate with minimal required fields."""
    content_data = {
        "book_id": "book123",
        "content_type": "section",
        "content": "This is a section of the book."
    }
    
    content = BookContentCreate(**content_data)
    
    assert content.book_id == "book123"
    assert content.content_type == "section"
    assert content.content == "This is a section of the book."
    assert content.chunk_index is None
    assert content.parent_id is None
    assert content.metadata is None


def test_book_content_required_fields():
    """Test that BookContentCreate requires all required fields."""
    # Missing book_id
    content_data = {
        "content_type": "chapter",
        "content": "This is the content."
    }
    
    with pytest.raises(ValueError):
        BookContentCreate(**content_data)
    
    # Missing content_type
    content_data = {
        "book_id": "book123",
        "content": "This is the content."
    }
    
    with pytest.raises(ValueError):
        BookContentCreate(**content_data)
    
    # Missing content
    content_data = {
        "book_id": "book123",
        "content_type": "chapter"
    }
    
    with pytest.raises(ValueError):
        BookContentCreate(**content_data)


def test_book_content_content_min_length():
    """Test that content must have minimum length."""
    content_data = {
        "book_id": "book123",
        "content_type": "chapter",
        "content": ""  # Empty content should fail
    }
    
    with pytest.raises(ValueError):
        BookContentCreate(**content_data)


def test_book_content_chunk_index_constraints():
    """Test chunk_index constraints."""
    # Test with negative chunk_index (should fail)
    content_data = {
        "book_id": "book123",
        "content_type": "chapter",
        "content": "This is the content.",
        "chunk_index": -1
    }
    
    with pytest.raises(ValueError):
        BookContentCreate(**content_data)
    
    # Test with valid chunk_index
    content_data = {
        "book_id": "book123",
        "content_type": "chapter",
        "content": "This is the content.",
        "chunk_index": 0  # Valid
    }
    
    content = BookContentCreate(**content_data)
    assert content.chunk_index == 0


def test_book_content_update_partial():
    """Test updating only some fields with BookContentUpdate."""
    content_update = BookContentUpdate(content="Updated content")
    
    assert content_update.content == "Updated content"
    assert content_update.chunk_index is None
    assert content_update.metadata is None


def test_book_content_indb_defaults():
    """Test that BookContentInDB has proper defaults."""
    content_data = {
        "book_id": "book123",
        "content_type": "paragraph",
        "content": "This is a paragraph of the book."
    }
    
    content = BookContentInDB(**content_data)
    
    assert content.book_id == "book123"
    assert content.content_type == "paragraph"
    assert content.content == "This is a paragraph of the book."
    assert content.id is not None  # UUID should be generated
    assert isinstance(content.created_at, datetime)
    assert isinstance(content.updated_at, datetime)


def test_book_content_model():
    """Test the public BookContent model."""
    content_data = {
        "book_id": "book123",
        "content_type": "section",
        "content": "This is a section of the book."
    }
    
    content = BookContent(**content_data)
    
    assert content.book_id == "book123"
    assert content.content_type == "section"
    assert content.content == "This is a section of the book."
    assert content.id is not None  # UUID should be generated
    assert isinstance(content.created_at, datetime)
    assert isinstance(content.updated_at, datetime)


def test_book_content_indb_with_optional_fields():
    """Test BookContentInDB with optional fields provided."""
    content_data = {
        "book_id": "book123",
        "content_type": "chapter",
        "content": "This is the content of the chapter.",
        "chunk_index": 5,
        "parent_id": "parent789",
        "page_number": 42,
        "section_title": "Introduction to AI",
        "vector_id": "vector_abc123",
        "metadata": {"key": "value"}
    }
    
    content = BookContentInDB(**content_data)
    
    assert content.book_id == "book123"
    assert content.content_type == "chapter"
    assert content.content == "This is the content of the chapter."
    assert content.chunk_index == 5
    assert content.parent_id == "parent789"
    assert content.page_number == 42
    assert content.section_title == "Introduction to AI"
    assert content.vector_id == "vector_abc123"
    assert content.metadata == {"key": "value"}


def test_book_content_page_number_constraints():
    """Test page_number constraints."""
    # Test with invalid page number
    content_data = {
        "book_id": "book123",
        "content_type": "chapter",
        "content": "This is the content.",
        "page_number": 0  # Invalid, should be ge=1
    }
    
    with pytest.raises(ValueError):
        BookContentInDB(**content_data)
    
    # Test with valid page number
    content_data = {
        "book_id": "book123",
        "content_type": "chapter",
        "content": "This is the content.",
        "page_number": 1  # Valid
    }
    
    content = BookContentInDB(**content_data)
    assert content.page_number == 1


def test_book_content_section_title_length():
    """Test section_title length constraints."""
    # Test with a very long section title
    content_data = {
        "book_id": "book123",
        "content_type": "chapter",
        "content": "This is the content.",
        "section_title": "A" * 201  # More than 200 characters
    }
    
    # This should fail validation
    with pytest.raises(ValueError):
        BookContentInDB(**content_data)