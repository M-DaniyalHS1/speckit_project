"""Service layer for reading session operations in AI-Enhanced Interactive Book Agent."""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
import uuid

from backend.src.models.sqlalchemy_models import ReadingSession as SQLAlchemyReadingSession, User, Book
from backend.src.models.reading_session import ReadingSession as PydanticReadingSession, ReadingSessionInDB


class SessionService:
    """Service class for handling reading session operations."""

    def __init__(self, db: AsyncSession):
        """Initialize the service with a database session."""
        self.db = db

    async def create_session(self, user_id: str, book_id: str) -> PydanticReadingSession:
        """Initialize a new reading session for a user with a book."""
        # First verify the user and book exist
        user_exists = await self.db.execute(
            select(User).filter(User.id == user_id)
        )
        user = user_exists.scalars().first()
        if not user:
            raise ValueError(f"User with id {user_id} does not exist")

        book_exists = await self.db.execute(
            select(Book).filter(Book.id == book_id)
        )
        book = book_exists.scalars().first()
        if not book:
            raise ValueError(f"Book with id {book_id} does not exist")

        # Check if there's an existing active session for this user-book combination
        existing_session_result = await self.db.execute(
            select(SQLAlchemyReadingSession)
            .filter(SQLAlchemyReadingSession.user_id == user_id)
            .filter(SQLAlchemyReadingSession.book_id == book_id)
            .filter(SQLAlchemyReadingSession.is_active == True)
        )
        existing_session = existing_session_result.scalars().first()

        if existing_session:
            # Reactivate the existing session
            stmt = (
                update(SQLAlchemyReadingSession)
                .where(SQLAlchemyReadingSession.id == existing_session.id)
                .values(
                    last_accessed_at=datetime.utcnow(),
                    is_active=True
                )
            )
            await self.db.execute(stmt)
            await self.db.commit()
            
            # Refresh and return the existing session
            await self.db.refresh(existing_session)
            return self._convert_sqlalchemy_to_pydantic(existing_session)
        else:
            # Create a new reading session
            db_session = SQLAlchemyReadingSession(
                user_id=user_id,
                book_id=book_id,
                current_location='1:1:1',  # Default to beginning: chapter:page:paragraph
                current_position_percent=0  # Start at 0% progress
            )

            self.db.add(db_session)
            await self.db.commit()
            await self.db.refresh(db_session)

        # Convert to Pydantic model and return
        return self._convert_sqlalchemy_to_pydantic(db_session)

    async def update_reading_position(
        self, 
        session_id: str, 
        current_location: str, 
        current_position_percent: Optional[int] = None
    ) -> Optional[PydanticReadingSession]:
        """Update the reading position in a session."""
        try:
            # Validate UUID format
            uuid.UUID(session_id)
        except ValueError:
            return None

        # Calculate position percent if not provided
        if current_position_percent is None:
            # Parse location to estimate percentage (this is a simplified calculation)
            # In a real app, this would be more sophisticated
            try:
                loc_parts = current_location.split(':')
                if len(loc_parts) >= 2:
                    # Simple estimation: assume 100 pages max, convert page to percentage
                    page_num = int(loc_parts[1]) if loc_parts[1].isdigit() else 1
                    current_position_percent = min(100, max(0, int((page_num / 100) * 100)))
            except:
                current_position_percent = 0

        # Update the database
        stmt = (
            update(SQLAlchemyReadingSession)
            .where(SQLAlchemyReadingSession.id == session_id)
            .values(
                current_location=current_location,
                current_position_percent=current_position_percent,
                last_accessed_at=datetime.utcnow()
            )
        )

        result = await self.db.execute(stmt)
        await self.db.commit()

        if result.rowcount > 0:
            # Return the updated session
            return await self.get_session_by_id(session_id)
        
        return None

    async def get_session_by_id(self, session_id: str) -> Optional[PydanticReadingSession]:
        """Get a specific reading session by ID."""
        try:
            # Validate UUID format
            uuid.UUID(session_id)
        except ValueError:
            return None

        result = await self.db.execute(
            select(SQLAlchemyReadingSession).filter(SQLAlchemyReadingSession.id == session_id)
        )
        session = result.scalars().first()

        if session:
            return self._convert_sqlalchemy_to_pydantic(session)
        return None

    async def get_reading_position(self, session_id: str) -> Optional[dict]:
        """Get only the reading position information for a session.

        Args:
            session_id: ID of the session to retrieve position for

        Returns:
            Dictionary with position information or None if session not found
        """
        try:
            # Validate UUID format
            uuid.UUID(session_id)
        except ValueError:
            return None

        result = await self.db.execute(
            select(SQLAlchemyReadingSession).filter(SQLAlchemyReadingSession.id == session_id)
        )
        session = result.scalars().first()

        if session:
            # Parse the location to extract components
            location_parts = session.current_location.split(':') if session.current_location else ['1', '1', '1']

            return {
                'session_id': str(session.id),
                'current_location': session.current_location,
                'current_chapter': location_parts[0] if len(location_parts) > 0 else '1',
                'current_page': int(location_parts[1]) if len(location_parts) > 1 and location_parts[1].isdigit() else 1,
                'current_paragraph': int(location_parts[2]) if len(location_parts) > 2 and location_parts[2].isdigit() else 1,
                'position_percent': session.current_position_percent or 0,
                'last_accessed_at': session.last_accessed_at
            }
        return None

    def _convert_sqlalchemy_to_pydantic(self, db_session: SQLAlchemyReadingSession) -> PydanticReadingSession:
        """
        Convert SQLAlchemy ReadingSession model to Pydantic ReadingSession model.
        This method handles the mapping between the two model types.
        """
        # Parse the location to extract chapter and position
        location_parts = db_session.current_location.split(':') if db_session.current_location else ['1', '1', '1']

        # Create Pydantic model with appropriate fields
        return PydanticReadingSession(
            id=str(db_session.id),
            user_id=str(db_session.user_id),
            book_id=str(db_session.book_id),
            current_position=int(location_parts[1]) if len(location_parts) > 1 and location_parts[1].isdigit() else 1,
            current_chapter=location_parts[0] if len(location_parts) > 0 else '1',
            current_location=db_session.current_location,
            current_position_percent=db_session.current_position_percent or 0,
            started_at=db_session.started_at,
            last_read_at=db_session.last_accessed_at or datetime.utcnow(),
            is_active=db_session.is_active,
            total_time_spent=0  # Not stored in DB, default to 0
        )