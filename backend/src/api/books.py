"""API endpoints for book management in the AI-Enhanced Interactive Book Agent."""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from backend.src.database import get_db_session
from backend.src.auth.security import get_current_user
from backend.src.models.sqlalchemy_models import User, Book as SQLAlchemyBook
from backend.src.models.book import Book as PydanticBook, BookCreate
from backend.src.services.book_service import BookService


# Create API router
router = APIRouter(
    prefix="/books",
    tags=["Books"],
    responses={404: {"description": "Not found"}}
)


@router.post("/", response_model=PydanticBook)
async def upload_book(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Upload a book file and create a book record in the database."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # Check if file extension is allowed
    allowed_extensions = ["pdf", "epub", "docx", "txt"]
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed types: {allowed_extensions}"
        )
    
    service = BookService(db)
    # Save the file and create a book record
    book = await service.create_book_record(
        user_id=current_user.id,
        file=file,
        file_extension=file_extension
    )
    
    return book


@router.get("/", response_model=List[PydanticBook])
async def get_user_books(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get all books for the current user."""
    service = BookService(db)
    return await service.get_user_books(current_user.id)


@router.get("/{book_id}", response_model=PydanticBook)
async def get_book(
    book_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific book by ID."""
    service = BookService(db)
    book = await service.get_book_by_id(book_id)
    
    if not book or str(book.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    return book


@router.delete("/{book_id}")
async def delete_book(
    book_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a book by ID."""
    service = BookService(db)
    book = await service.get_book_by_id(book_id)
    
    if not book or str(book.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    await service.delete_book(book_id)
    return {"message": "Book deleted successfully"}


@router.post("/{book_id}/process")
async def process_book(
    book_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Start processing a book for content extraction and indexing."""
    service = BookService(db)
    book = await service.get_book_by_id(book_id)
    
    if not book or str(book.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Start the processing task
    await service.process_book_content(book_id)
    
    return {"message": f"Processing started for book {book_id}"}


@router.get("/{book_id}/status")
async def get_book_processing_status(
    book_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get the processing status of a book."""
    service = BookService(db)
    book = await service.get_book_by_id(book_id)
    
    if not book or str(book.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    return {
        "book_id": book_id,
        "is_processed": book.is_processed,
        "processing_error": book.processing_error
    }