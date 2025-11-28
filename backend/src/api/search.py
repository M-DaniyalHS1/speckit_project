"""API endpoints for book content search in the AI-Enhanced Interactive Book Agent."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from backend.src.database import get_db_session
from backend.src.auth.security import get_current_user
from backend.src.models.sqlalchemy_models import User, Book
from backend.src.models.query import Query as PydanticQuery, QueryCreate
from backend.src.services.search_service import SearchService


# Create API router
router = APIRouter(
    prefix="/search",
    tags=["Search"],
    responses={404: {"description": "Not found"}}
)


@router.post("/", response_model=List[dict])
async def search_book_content(
    query_data: QueryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Search for content within a user's book using semantic search."""
    # Verify the user has access to the book
    book_result = await db.execute(
        select(Book).filter(Book.id == query_data.book_id, Book.user_id == current_user.id)
    )
    book = book_result.scalars().first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found or access denied"
        )
    
    service = SearchService(db)
    results = await service.search_content(query_data.book_id, query_data.query_text)
    
    return results


@router.post("/global", response_model=List[dict])
async def global_search(
    query_data: QueryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Search for content across all of the user's books."""
    service = SearchService(db)
    results = await service.global_search(current_user.id, query_data.query_text)
    
    return results


@router.get("/history/{book_id}", response_model=List[PydanticQuery])
async def get_search_history(
    book_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get search history for a specific book."""
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
    
    service = SearchService(db)
    history = await service.get_search_history(book_id)
    
    return history