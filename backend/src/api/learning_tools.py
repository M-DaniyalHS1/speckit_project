"""API endpoints for learning tools in the AI-Enhanced Interactive Book Agent."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from backend.src.database import get_db_session
from backend.src.auth.security import get_current_user
from backend.src.models.sqlalchemy_models import User, Book
from backend.src.models.learning_material import LearningMaterial as PydanticLearningMaterial, LearningMaterialCreate
from backend.src.services.learning_tool_service import LearningToolService


# Create API router
router = APIRouter(
    prefix="/learning-tools",
    tags=["Learning Tools"],
    responses={404: {"description": "Not found"}}
)


@router.post("/", response_model=PydanticLearningMaterial)
async def create_learning_material(
    material_data: LearningMaterialCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a learning material (quiz, flashcard, note, etc.) for a book."""
    # Verify the user has access to the book
    book_result = await db.execute(
        select(Book).filter(Book.id == material_data.book_id, Book.user_id == current_user.id)
    )
    book = book_result.scalars().first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found or access denied"
        )
    
    service = LearningToolService(db)
    material = await service.create_learning_material(
        current_user.id,
        material_data.book_id,
        material_data.material_type,
        material_data.title,
        material_data.content,
        material_data.metadata
    )
    
    return material


@router.get("/", response_model=List[PydanticLearningMaterial])
async def get_learning_materials(
    book_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get all learning materials for a specific book."""
    # Verify the user has access to the book
    book_result = await db.execute(
        select(Book).filter(Book.id == book_id, Book.user_id == current_user.id)
    )
    book = book_result.scalars().first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found or access denied"
        )
    
    service = LearningToolService(db)
    materials = await service.get_learning_materials_for_book(book_id)
    
    return materials


@router.get("/{material_id}", response_model=PydanticLearningMaterial)
async def get_learning_material(
    material_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific learning material by ID."""
    service = LearningToolService(db)
    material = await service.get_learning_material_by_id(material_id)
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning material not found"
        )
    
    # Verify the user has access to this material
    # In a real implementation, we would check the material's ownership
    if str(material.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this learning material"
        )
    
    return material


@router.post("/generate-quiz")
async def generate_quiz(
    request_data: dict,  # Contains book_id, content_id (optional), num_questions
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate a quiz for specific book content using AI."""
    book_id = request_data.get('book_id')
    content_id = request_data.get('content_id')  # Optional - if not provided, quiz covers entire book
    num_questions = request_data.get('num_questions', 5)
    
    # Verify the user has access to the book
    book_result = await db.execute(
        select(Book).filter(Book.id == book_id, Book.user_id == current_user.id)
    )
    book = book_result.scalars().first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found or access denied"
        )
    
    service = LearningToolService(db)
    quiz = await service.generate_quiz(
        current_user.id,
        book_id,
        content_id,
        num_questions
    )
    
    return quiz


@router.post("/generate-flashcards")
async def generate_flashcards(
    request_data: dict,  # Contains book_id, content_id (optional)
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate flashcards for specific book content using AI."""
    book_id = request_data.get('book_id')
    content_id = request_data.get('content_id')  # Optional - if not provided, flashcards cover entire book
    
    # Verify the user has access to the book
    book_result = await db.execute(
        select(Book).filter(Book.id == book_id, Book.user_id == current_user.id)
    )
    book = book_result.scalars().first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found or access denied"
        )
    
    service = LearningToolService(db)
    flashcards = await service.generate_flashcards(
        current_user.id,
        book_id,
        content_id
    )
    
    return flashcards