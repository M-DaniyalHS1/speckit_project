"""API endpoints for content summarization in the AI-Enhanced Interactive Book Agent."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.database import get_db_session
from backend.src.auth.security import get_current_user
from backend.src.models.sqlalchemy_models import User, Book, BookContent
from backend.src.models.learning_material import LearningMaterial as PydanticLearningMaterial, LearningMaterialCreate
from backend.src.services.summarization_service import SummarizationService


# Create API router
router = APIRouter(
    prefix="/summaries",
    tags=["Summaries"],
    responses={404: {"description": "Not found"}}
)


@router.post("/", response_model=PydanticLearningMaterial)
async def create_summary(
    summary_data: LearningMaterialCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a summary for specific book content."""
    # Verify the user has access to the book
    book_result = await db.execute(
        select(Book).filter(Book.id == summary_data.book_id, Book.user_id == current_user.id)
    )
    book = book_result.scalars().first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found or access denied"
        )
    
    # Ensure the material type is summary
    summary_data.material_type = "summary"
    
    service = SummarizationService(db)
    summary = await service.create_summary(
        current_user.id,
        summary_data.book_id,
        summary_data.content_id,
        summary_data.title,
        summary_data.content
    )
    
    return summary


@router.post("/generate")
async def generate_summary(
    request_data: dict,  # Contains content_id and summary_type
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate a summary for specific book content using AI."""
    content_id = request_data.get('content_id')
    summary_type = request_data.get('summary_type', 'section')  # section, chapter, book
    
    # Verify the user has access to the content
    content_result = await db.execute(
        select(BookContent)
        .join(Book)
        .filter(BookContent.id == content_id, Book.user_id == current_user.id)
    )
    content = content_result.scalars().first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found or access denied"
        )
    
    service = SummarizationService(db)
    summary = await service.generate_summary(
        current_user.id,
        content.book_id,
        content_id,
        summary_type
    )
    
    return summary