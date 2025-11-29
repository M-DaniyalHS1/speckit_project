"""API endpoints for reading sessions in the AI-Enhanced Interactive Book Agent."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import Field

from backend.src.database import get_db_session
from backend.src.auth.security import get_current_user
from backend.src.models.sqlalchemy_models import User
from backend.src.models.reading_session import ReadingSession as PydanticReadingSession, ReadingSessionCreate, ReadingSessionUpdate
from backend.src.services.session_service import SessionService


# Create API router
router = APIRouter(
    prefix="/sessions",
    tags=["Reading Sessions"],
    responses={404: {"description": "Not found"}}
)


@router.post("/", response_model=PydanticReadingSession)
async def initialize_reading_session(
    session_data: ReadingSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Initialize a reading session for the current user with a book.

    This endpoint creates a new reading session or resumes an existing one
    for the specified book."""
    service = SessionService(db)
    return await service.create_session(current_user.id, session_data.book_id)


@router.get("/", response_model=List[PydanticReadingSession])
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get all reading sessions for the current user."""
    # We need to query the database directly since SessionService doesn't have this method
    from sqlalchemy.future import select
    from backend.src.models.sqlalchemy_models import ReadingSession as SQLAlchemyReadingSession

    result = await db.execute(
        select(SQLAlchemyReadingSession).filter(SQLAlchemyReadingSession.user_id == current_user.id)
    )
    sessions = result.scalars().all()

    # Convert to Pydantic models
    from backend.src.services.session_service import SessionService
    service = SessionService(db)
    return [service._convert_sqlalchemy_to_pydantic(session) for session in sessions]


@router.get("/{session_id}", response_model=PydanticReadingSession)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific reading session by ID."""
    service = SessionService(db)
    session = await service.get_session_by_id(session_id)

    if not session or str(session.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return session


from pydantic import BaseModel
from typing import Optional


class UpdateReadingPositionRequest(BaseModel):
    """Request model for updating reading position."""
    current_location: Optional[str] = Field(None, description="Current reading location (chapter:page:paragraph)")
    position_percent: Optional[int] = Field(None, ge=0, le=100, description="Reading progress as percentage (0-100)")


@router.put("/{session_id}/position", response_model=PydanticReadingSession)
async def update_reading_position(
    session_id: str,
    position_data: UpdateReadingPositionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update the current reading position in a session."""
    service = SessionService(db)
    session = await service.get_session_by_id(session_id)

    if not session or str(session.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Use provided values or fall back to current session values
    current_location = position_data.current_location or session.current_location
    current_position_percent = position_data.position_percent

    # Update the reading position
    updated_session = await service.update_reading_position(
        session_id,
        current_location,
        current_position_percent
    )

    if not updated_session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update reading position"
        )

    return updated_session


class ReadingPositionResponse(BaseModel):
    """Response model for reading position information."""
    session_id: str
    current_location: str
    current_chapter: str
    current_page: int
    current_paragraph: int
    position_percent: int
    last_accessed_at: datetime


@router.get("/{session_id}/position", response_model=ReadingPositionResponse)
async def get_current_reading_position(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get the current reading position for a session."""
    service = SessionService(db)
    position_info = await service.get_reading_position(session_id)

    if not position_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Verify that the session belongs to the current user
    # Get the full session to check user ownership
    session = await service.get_session_by_id(session_id)
    if not session or str(session.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return ReadingPositionResponse(**position_info)


@router.put("/{session_id}/activate")
async def activate_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Activate a reading session."""
    service = SessionService(db)
    session = await service.get_session_by_id(session_id)

    if not session or str(session.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Since we're using the updated SessionService, we need to handle this differently
    # For now, we'll just return a success message since the activate/deactivate methods
    # are not in SessionService
    from sqlalchemy import update
    from backend.src.models.sqlalchemy_models import ReadingSession as SQLAlchemyReadingSession

    stmt = (
        update(SQLAlchemyReadingSession)
        .where(SQLAlchemyReadingSession.id == session_id)
        .values(is_active=True)
    )
    await db.execute(stmt)
    await db.commit()

    return {"message": "Session activated successfully"}


@router.put("/{session_id}/deactivate")
async def deactivate_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Deactivate a reading session."""
    service = SessionService(db)
    session = await service.get_session_by_id(session_id)

    if not session or str(session.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Since we're using the updated SessionService, we need to handle this differently
    # For now, we'll just return a success message since the activate/deactivate methods
    # are not in SessionService
    from sqlalchemy import update
    from backend.src.models.sqlalchemy_models import ReadingSession as SQLAlchemyReadingSession

    stmt = (
        update(SQLAlchemyReadingSession)
        .where(SQLAlchemyReadingSession.id == session_id)
        .values(is_active=False)
    )
    await db.execute(stmt)
    await db.commit()

    return {"message": "Session deactivated successfully"}


@router.get("/{session_id}/save")
async def save_reading_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Save the current reading session state for later restoration."""
    service = SessionService(db)
    session = await service.get_session_by_id(session_id)

    if not session or str(session.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # In a real implementation, this would store the session state to a cache
    # or create a snapshot of the session for later restoration.
    # For now, we'll just return the session data that would be saved.

    return {
        "session_id": session.id,
        "user_id": session.user_id,
        "book_id": session.book_id,
        "current_location": session.current_location,
        "current_position_percent": session.current_position_percent,
        "last_accessed_at": session.last_read_at,
        "saved_at": datetime.utcnow().isoformat()
    }


@router.post("/{session_id}/restore")
async def restore_reading_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Restore a previously saved reading session."""
    service = SessionService(db)
    session = await service.get_session_by_id(session_id)

    if not session or str(session.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # In a real implementation, this would restore the session state from a cache
    # or snapshot. For now, we'll just return the session as is, but the endpoint
    # indicates the capability to restore a session.

    # Reactivate the session if it was inactive
    from sqlalchemy import update
    from backend.src.models.sqlalchemy_models import ReadingSession as SQLAlchemyReadingSession

    stmt = (
        update(SQLAlchemyReadingSession)
        .where(SQLAlchemyReadingSession.id == session_id)
        .values(is_active=True, last_accessed_at=datetime.utcnow())
    )
    await db.execute(stmt)
    await db.commit()

    # Refresh and return the session
    restored_session = await service.get_session_by_id(session_id)

    return {
        "session_id": restored_session.id,
        "user_id": restored_session.user_id,
        "book_id": restored_session.book_id,
        "current_location": restored_session.current_location,
        "current_position_percent": restored_session.current_position_percent,
        "restored_at": datetime.utcnow().isoformat()
    }