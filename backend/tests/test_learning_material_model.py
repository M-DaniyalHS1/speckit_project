"""Unit tests for the LearningMaterial model in the AI-Enhanced Interactive Book Agent.

This module contains comprehensive unit tests for all LearningMaterial model components,
including validation, creation, and field constraints.
"""
import pytest
from datetime import datetime
from backend.src.models.learning_material import LearningMaterialCreate, LearningMaterialUpdate, LearningMaterialInDB, LearningMaterial


def test_learning_material_create_valid():
    """Test creating a valid LearningMaterialCreate instance."""
    material_data = {
        "user_id": "user123",
        "book_id": "book456",
        "title": "Vocabulary Flashcards",
        "material_type": "flashcard"
    }
    
    material = LearningMaterialCreate(**material_data)
    
    assert material.user_id == "user123"
    assert material.book_id == "book456"
    assert material.title == "Vocabulary Flashcards"
    assert material.material_type == "flashcard"


def test_learning_material_create_minimal():
    """Test creating a LearningMaterialCreate with minimal required fields."""
    material_data = {
        "user_id": "user123",
        "book_id": "book456",
        "title": "My Notes",
        "material_type": "note"
    }
    
    material = LearningMaterialCreate(**material_data)
    
    assert material.user_id == "user123"
    assert material.book_id == "book456"
    assert material.title == "My Notes"
    assert material.material_type == "note"
    assert material.content is None
    assert material.metadata is None


def test_learning_material_required_fields():
    """Test that LearningMaterialCreate requires all required fields."""
    # Missing user_id
    material_data = {
        "book_id": "book456",
        "title": "Quiz",
        "material_type": "quiz"
    }
    
    with pytest.raises(ValueError):
        LearningMaterialCreate(**material_data)
    
    # Missing book_id
    material_data = {
        "user_id": "user123",
        "title": "Quiz",
        "material_type": "quiz"
    }
    
    with pytest.raises(ValueError):
        LearningMaterialCreate(**material_data)
    
    # Missing title
    material_data = {
        "user_id": "user123",
        "book_id": "book456",
        "material_type": "quiz"
    }
    
    with pytest.raises(ValueError):
        LearningMaterialCreate(**material_data)
    
    # Missing material_type
    material_data = {
        "user_id": "user123",
        "book_id": "book456",
        "title": "Quiz"
    }
    
    with pytest.raises(ValueError):
        LearningMaterialCreate(**material_data)


def test_learning_material_title_length_constraints():
    """Test title length constraints."""
    # Test with a very long title
    material_data = {
        "user_id": "user123",
        "book_id": "book456",
        "title": "A" * 201,  # More than 200 characters
        "material_type": "summary"
    }
    
    with pytest.raises(ValueError):
        LearningMaterialCreate(**material_data)
    
    # Test with empty title
    material_data = {
        "user_id": "user123",
        "book_id": "book456",
        "title": "",
        "material_type": "summary"
    }
    
    with pytest.raises(ValueError):
        LearningMaterialCreate(**material_data)


def test_learning_material_update_partial():
    """Test updating only some fields with LearningMaterialUpdate."""
    material_update = LearningMaterialUpdate(title="Updated Title")
    
    assert material_update.title == "Updated Title"
    assert material_update.content is None
    assert material_update.metadata is None


def test_learning_material_indb_defaults():
    """Test that LearningMaterialInDB has proper defaults."""
    material_data = {
        "user_id": "user123",
        "book_id": "book456",
        "title": "Chapter Summary",
        "material_type": "summary"
    }
    
    material = LearningMaterialInDB(**material_data)
    
    assert material.user_id == "user123"
    assert material.book_id == "book456"
    assert material.title == "Chapter Summary"
    assert material.material_type == "summary"
    assert material.id is not None  # UUID should be generated
    assert material.is_active is True  # Default value
    assert isinstance(material.created_at, datetime)
    assert isinstance(material.updated_at, datetime)


def test_learning_material_model():
    """Test the public LearningMaterial model."""
    material_data = {
        "user_id": "user123",
        "book_id": "book456",
        "title": "Practice Questions",
        "material_type": "quiz"
    }
    
    material = LearningMaterial(**material_data)
    
    assert material.user_id == "user123"
    assert material.book_id == "book456"
    assert material.title == "Practice Questions"
    assert material.material_type == "quiz"
    assert material.id is not None  # UUID should be generated
    assert material.is_active is True  # Default value
    assert isinstance(material.created_at, datetime)
    assert isinstance(material.updated_at, datetime)


def test_learning_material_indb_with_optional_fields():
    """Test LearningMaterialInDB with optional fields provided."""
    material_data = {
        "user_id": "user123",
        "book_id": "book456",
        "title": "Key Concepts from Chapter 3",
        "material_type": "summary",
        "content": "This is the summary content...",
        "is_active": False,
        "metadata": {"difficulty": "medium", "tags": ["AI", "ML"], "created_from": "section_3_2"}
    }
    
    material = LearningMaterialInDB(**material_data)
    
    assert material.user_id == "user123"
    assert material.book_id == "book456"
    assert material.title == "Key Concepts from Chapter 3"
    assert material.material_type == "summary"
    assert material.content == "This is the summary content..."
    assert material.is_active is False
    assert material.metadata == {"difficulty": "medium", "tags": ["AI", "ML"], "created_from": "section_3_2"}


def test_learning_material_type_values():
    """Test different material types."""
    valid_types = ["quiz", "flashcard", "note", "summary"]
    
    for material_type in valid_types:
        material_data = {
            "user_id": "user123",
            "book_id": "book456",
            "title": f"My {material_type}",
            "material_type": material_type
        }
        
        material = LearningMaterialCreate(**material_data)
        assert material.material_type == material_type


def test_learning_material_metadata():
    """Test that metadata can contain various types of data."""
    material_data = {
        "user_id": "user123",
        "book_id": "book456",
        "title": "Detailed Notes",
        "material_type": "note",
        "metadata": {
            "created_by_ai": True,
            "sections_covered": [1, 2, 3],
            "accuracy_rating": 0.95,
            "review_dates": ["2023-01-15", "2023-02-20"],
            "related_materials": ["material_789", "material_101"]
        }
    }
    
    material = LearningMaterialCreate(**material_data)
    expected_metadata = {
        "created_by_ai": True,
        "sections_covered": [1, 2, 3],
        "accuracy_rating": 0.95,
        "review_dates": ["2023-01-15", "2023-02-20"],
        "related_materials": ["material_789", "material_101"]
    }
    assert material.metadata == expected_metadata


def test_learning_material_is_active():
    """Test the is_active field."""
    material_data = {
        "user_id": "user123",
        "book_id": "book456",
        "title": "Archived Quiz",
        "material_type": "quiz",
        "is_active": False
    }
    
    material = LearningMaterialInDB(**material_data)
    assert material.is_active is False