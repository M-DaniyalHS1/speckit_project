"""Unit tests for the Book model in the AI-Enhanced Interactive Book Agent.

This module contains comprehensive unit tests for all Book model components,
including validation, creation, and field constraints.
"""
import pytest
from datetime import datetime
from backend.src.models.book import BookCreate, BookUpdate, BookInDB, Book


def test_book_create_valid():
    """Test creating a valid BookCreate instance."""
    book_data = {
        "title": "Test Book Title",
        "author": "Test Author",
        "description": "A brief description of the test book",
        "isbn": "1234567890123"
    }
    
    book = BookCreate(**book_data)
    
    assert book.title == "Test Book Title"
    assert book.author == "Test Author"
    assert book.description == "A brief description of the test book"
    assert book.isbn == "1234567890123"


def test_book_create_minimal():
    """Test creating a BookCreate with minimal required fields."""
    book_data = {
        "title": "Minimal Book",
        "author": "Minimal Author"
    }
    
    book = BookCreate(**book_data)
    
    assert book.title == "Minimal Book"
    assert book.author == "Minimal Author"
    assert book.description is None
    assert book.isbn is None


def test_book_title_length_constraints():
    """Test title length constraints."""
    # Test with a very long title (should fail)
    book_data = {
        "title": "A" * 201,  # More than 200 characters
        "author": "Test Author"
    }
    
    with pytest.raises(ValueError):
        BookCreate(**book_data)
    
    # Test with empty title (should fail)
    book_data = {
        "title": "",
        "author": "Test Author"
    }
    
    with pytest.raises(ValueError):
        BookCreate(**book_data)


def test_book_author_length_constraints():
    """Test author length constraints."""
    # Test with a very long author name (should fail)
    book_data = {
        "title": "Test Book",
        "author": "A" * 101  # More than 100 characters
    }
    
    with pytest.raises(ValueError):
        BookCreate(**book_data)
    
    # Test with empty author (should fail)
    book_data = {
        "title": "Test Book",
        "author": ""
    }
    
    with pytest.raises(ValueError):
        BookCreate(**book_data)


def test_book_isbn_length_constraints():
    """Test ISBN length constraints."""
    # Test with a very long ISBN (should fail)
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "1" * 14  # More than 13 characters
    }

    with pytest.raises(ValueError):
        BookCreate(**book_data)


def test_book_description_length_constraints():
    """Test description length constraints."""
    # Test with a very long description (should fail)
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "description": "A" * 1001  # More than 1000 characters
    }
    
    with pytest.raises(ValueError):
        BookCreate(**book_data)


def test_book_update_partial():
    """Test updating only some fields with BookUpdate."""
    book_update = BookUpdate(title="Updated Title")
    
    assert book_update.title == "Updated Title"
    assert book_update.author is None
    assert book_update.description is None


def test_book_indb_defaults():
    """Test that BookInDB has proper defaults."""
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "user_id": "user123"
    }
    
    book = BookInDB(**book_data)
    
    assert book.title == "Test Book"
    assert book.author == "Test Author"
    assert book.user_id == "user123"
    assert book.id is not None  # UUID should be generated
    assert book.is_processed is False
    assert isinstance(book.created_at, datetime)
    assert isinstance(book.updated_at, datetime)


def test_book_model():
    """Test the public Book model."""
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "user_id": "user123"
    }
    
    book = Book(**book_data)
    
    assert book.title == "Test Book"
    assert book.author == "Test Author"
    assert book.user_id == "user123"
    assert book.id is not None  # UUID should be generated
    assert book.is_processed is False
    assert isinstance(book.created_at, datetime)
    assert isinstance(book.updated_at, datetime)


def test_book_indb_with_optional_fields():
    """Test BookInDB with optional fields provided."""
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "user_id": "user123",
        "description": "A detailed description",
        "file_type": "PDF",
        "page_count": 300,
        "word_count": 75000,
        "is_processed": True
    }
    
    book = BookInDB(**book_data)
    
    assert book.title == "Test Book"
    assert book.author == "Test Author"
    assert book.user_id == "user123"
    assert book.description == "A detailed description"
    assert book.file_type == "PDF"
    assert book.page_count == 300
    assert book.word_count == 75000
    assert book.is_processed is True


def test_book_page_count_constraints():
    """Test page count constraints in BookInDB."""
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "user_id": "user123",
        "page_count": -1  # Invalid page count
    }
    
    with pytest.raises(ValueError):
        BookInDB(**book_data)


def test_book_word_count_constraints():
    """Test word count constraints in BookInDB."""
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "user_id": "user123",
        "word_count": -1  # Invalid word count
    }
    
    with pytest.raises(ValueError):
        BookInDB(**book_data)