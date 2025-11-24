"""Unit tests for the Explanation model in the AI-Enhanced Interactive Book Agent.

This module contains comprehensive unit tests for all Explanation model components,
including validation, creation, and field constraints.
"""
import pytest
from datetime import datetime
from backend.src.models.explanation import ExplanationCreate, ExplanationUpdate, ExplanationInDB, Explanation


def test_explanation_create_valid():
    """Test creating a valid ExplanationCreate instance."""
    explanation_data = {
        "query_id": "query123",
        "book_id": "book456",
        "content": "This is a detailed explanation of the concept."
    }
    
    explanation = ExplanationCreate(**explanation_data)
    
    assert explanation.query_id == "query123"
    assert explanation.book_id == "book456"
    assert explanation.content == "This is a detailed explanation of the concept."


def test_explanation_create_minimal():
    """Test creating an ExplanationCreate with minimal required fields."""
    explanation_data = {
        "query_id": "query123",
        "book_id": "book456",
        "content": "This is an explanation."
    }
    
    explanation = ExplanationCreate(**explanation_data)
    
    assert explanation.query_id == "query123"
    assert explanation.book_id == "book456"
    assert explanation.content == "This is an explanation."
    assert explanation.explanation_type == "detailed"  # Default value
    assert explanation.source_content_ids is None
    assert explanation.complexity_level == "medium"  # Default value


def test_explanation_required_fields():
    """Test that ExplanationCreate requires all required fields."""
    # Missing query_id
    explanation_data = {
        "book_id": "book456",
        "content": "This is an explanation."
    }
    
    with pytest.raises(ValueError):
        ExplanationCreate(**explanation_data)
    
    # Missing book_id
    explanation_data = {
        "query_id": "query123",
        "content": "This is an explanation."
    }
    
    with pytest.raises(ValueError):
        ExplanationCreate(**explanation_data)
    
    # Missing content
    explanation_data = {
        "query_id": "query123",
        "book_id": "book456"
    }
    
    with pytest.raises(ValueError):
        ExplanationCreate(**explanation_data)


def test_explanation_content_min_length():
    """Test that content must have minimum length."""
    explanation_data = {
        "query_id": "query123",
        "book_id": "book456",
        "content": ""  # Empty content should fail
    }
    
    with pytest.raises(ValueError):
        ExplanationCreate(**explanation_data)


def test_explanation_update_partial():
    """Test updating only some fields with ExplanationUpdate."""
    explanation_update = ExplanationUpdate(content="Updated explanation content")
    
    assert explanation_update.content == "Updated explanation content"


def test_explanation_indb_defaults():
    """Test that ExplanationInDB has proper defaults."""
    explanation_data = {
        "query_id": "query123",
        "book_id": "book456",
        "content": "This is an explanation of the concept."
    }
    
    explanation = ExplanationInDB(**explanation_data)
    
    assert explanation.query_id == "query123"
    assert explanation.book_id == "book456"
    assert explanation.content == "This is an explanation of the concept."
    assert explanation.id is not None  # UUID should be generated
    assert explanation.explanation_type == "detailed"  # Default value
    assert explanation.complexity_level == "medium"  # Default value
    assert isinstance(explanation.created_at, datetime)
    assert isinstance(explanation.updated_at, datetime)


def test_explanation_model():
    """Test the public Explanation model."""
    explanation_data = {
        "query_id": "query123",
        "book_id": "book456",
        "content": "This is an explanation."
    }
    
    explanation = Explanation(**explanation_data)
    
    assert explanation.query_id == "query123"
    assert explanation.book_id == "book456"
    assert explanation.content == "This is an explanation."
    assert explanation.id is not None  # UUID should be generated
    assert explanation.explanation_type == "detailed"  # Default value
    assert explanation.complexity_level == "medium"  # Default value
    assert isinstance(explanation.created_at, datetime)
    assert isinstance(explanation.updated_at, datetime)


def test_explanation_indb_with_optional_fields():
    """Test ExplanationInDB with optional fields provided."""
    explanation_data = {
        "query_id": "query123",
        "book_id": "book456",
        "content": "This is a comprehensive explanation.",
        "explanation_type": "simple",
        "source_content_ids": ["content1", "content2", "content3"],
        "complexity_level": "high"
    }
    
    explanation = ExplanationInDB(**explanation_data)
    
    assert explanation.query_id == "query123"
    assert explanation.book_id == "book456"
    assert explanation.content == "This is a comprehensive explanation."
    assert explanation.explanation_type == "simple"
    assert explanation.source_content_ids == ["content1", "content2", "content3"]
    assert explanation.complexity_level == "high"


def test_explanation_type_values():
    """Test different explanation types."""
    explanation_data = {
        "query_id": "query123",
        "book_id": "book456",
        "content": "This is a simple explanation.",
        "explanation_type": "simple"
    }
    
    explanation = ExplanationCreate(**explanation_data)
    assert explanation.explanation_type == "simple"
    
    explanation_data["explanation_type"] = "detailed"
    explanation = ExplanationCreate(**explanation_data)
    assert explanation.explanation_type == "detailed"


def test_explanation_complexity_level_values():
    """Test different complexity levels."""
    explanation_data = {
        "query_id": "query123",
        "book_id": "book456",
        "content": "This is an explanation.",
        "complexity_level": "low"
    }
    
    explanation = ExplanationCreate(**explanation_data)
    assert explanation.complexity_level == "low"
    
    explanation_data["complexity_level"] = "high"
    explanation = ExplanationCreate(**explanation_data)
    assert explanation.complexity_level == "high"


def test_source_content_ids_list():
    """Test that source_content_ids can be a list of content IDs."""
    explanation_data = {
        "query_id": "query123",
        "book_id": "book456",
        "content": "This explanation uses multiple sources.",
        "source_content_ids": ["src1", "src2", "src3", "src4"]
    }
    
    explanation = ExplanationCreate(**explanation_data)
    assert explanation.source_content_ids == ["src1", "src2", "src3", "src4"]