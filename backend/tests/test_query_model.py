"""Unit tests for the Query model in the AI-Enhanced Interactive Book Agent.

This module contains comprehensive unit tests for all Query model components,
including validation, creation, and field constraints.
"""
import pytest
from datetime import datetime
from backend.src.models.query import QueryCreate, QueryUpdate, QueryInDB, Query


def test_query_create_valid():
    """Test creating a valid QueryCreate instance."""
    query_data = {
        "user_id": "user123",
        "book_id": "book456",
        "query_text": "What is the main theme of this book?"
    }
    
    query = QueryCreate(**query_data)
    
    assert query.user_id == "user123"
    assert query.book_id == "book456"
    assert query.query_text == "What is the main theme of this book?"


def test_query_create_minimal():
    """Test creating a QueryCreate with minimal required fields."""
    query_data = {
        "user_id": "user123",
        "book_id": "book456",
        "query_text": "Explain this concept."
    }
    
    query = QueryCreate(**query_data)
    
    assert query.user_id == "user123"
    assert query.book_id == "book456"
    assert query.query_text == "Explain this concept."
    assert query.query_type == "general"  # Default value
    assert query.context is None


def test_query_required_fields():
    """Test that QueryCreate requires all required fields."""
    # Missing user_id
    query_data = {
        "book_id": "book456",
        "query_text": "What is this?"
    }
    
    with pytest.raises(ValueError):
        QueryCreate(**query_data)
    
    # Missing book_id
    query_data = {
        "user_id": "user123",
        "query_text": "What is this?"
    }
    
    with pytest.raises(ValueError):
        QueryCreate(**query_data)
    
    # Missing query_text
    query_data = {
        "user_id": "user123",
        "book_id": "book456"
    }
    
    with pytest.raises(ValueError):
        QueryCreate(**query_data)


def test_query_text_length_constraints():
    """Test query_text length constraints."""
    # Test with empty query_text
    query_data = {
        "user_id": "user123",
        "book_id": "book456",
        "query_text": ""
    }
    
    with pytest.raises(ValueError):
        QueryCreate(**query_data)
    
    # Test with very long query_text
    query_data = {
        "user_id": "user123",
        "book_id": "book456",
        "query_text": "A" * 1001  # More than 1000 characters
    }
    
    with pytest.raises(ValueError):
        QueryCreate(**query_data)


def test_query_update_partial():
    """Test updating only some fields with QueryUpdate."""
    query_update = QueryUpdate(query_text="Updated query text")
    
    assert query_update.query_text == "Updated query text"


def test_query_indb_defaults():
    """Test that QueryInDB has proper defaults."""
    query_data = {
        "user_id": "user123",
        "book_id": "book456",
        "query_text": "What is machine learning?"
    }
    
    query = QueryInDB(**query_data)
    
    assert query.user_id == "user123"
    assert query.book_id == "book456"
    assert query.query_text == "What is machine learning?"
    assert query.id is not None  # UUID should be generated
    assert query.query_type == "general"  # Default value
    assert isinstance(query.created_at, datetime)
    assert isinstance(query.updated_at, datetime)


def test_query_model():
    """Test the public Query model."""
    query_data = {
        "user_id": "user123",
        "book_id": "book456",
        "query_text": "How does this work?"
    }
    
    query = Query(**query_data)
    
    assert query.user_id == "user123"
    assert query.book_id == "book456"
    assert query.query_text == "How does this work?"
    assert query.id is not None  # UUID should be generated
    assert query.query_type == "general"  # Default value
    assert isinstance(query.created_at, datetime)
    assert isinstance(query.updated_at, datetime)


def test_query_indb_with_optional_fields():
    """Test QueryInDB with optional fields provided."""
    query_data = {
        "user_id": "user123",
        "book_id": "book456",
        "query_text": "Explain the algorithm in detail.",
        "query_type": "explanation",
        "context": "Related to chapter 3, section 2"
    }
    
    query = QueryInDB(**query_data)
    
    assert query.user_id == "user123"
    assert query.book_id == "book456"
    assert query.query_text == "Explain the algorithm in detail."
    assert query.query_type == "explanation"
    assert query.context == "Related to chapter 3, section 2"


def test_query_type_assignment():
    """Test different query types."""
    query_data = {
        "user_id": "user123",
        "book_id": "book456",
        "query_text": "Find information about neural networks.",
        "query_type": "search"
    }
    
    query = QueryCreate(**query_data)
    assert query.query_type == "search"


def test_query_context_optional():
    """Test that context is optional in QueryCreate."""
    query_data = {
        "user_id": "user123",
        "book_id": "book456",
        "query_text": "Summarize this chapter."
    }
    
    query = QueryCreate(**query_data)
    assert query.context is None