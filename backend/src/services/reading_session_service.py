"""Service layer for reading session operations in AI-Enhanced Interactive Book Agent."""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
import uuid

from backend.src.models.sqlalchemy_models import ReadingSession as SQLAlchemyReadingSession, User, Book
from backend.src.models.reading_session import ReadingSession as PydanticReadingSession, ReadingSessionInDB


class ReadingSessionService:
    """Service class for handling reading session operations."""

    def __init__(self, db: AsyncSession):
        """Initialize the service with a database session."""
        self.db = db

    async def create_session(self, user_id: str, session_data: dict) -> PydanticReadingSession:
        """Create a new reading session."""
        # First verify the user and book exist
        user_exists = await self.db.execute(
            select(User).filter(User.id == user_id)
        )
        user = user_exists.scalars().first()
        if not user:
            raise ValueError(f"User with id {user_id} does not exist")

        book_exists = await self.db.execute(
            select(Book).filter(Book.id == session_data.get('book_id'))
        )
        book = book_exists.scalars().first()
        if not book:
            raise ValueError(f"Book with id {session_data.get('book_id')} does not exist")

        # Create the reading session
        db_session = SQLAlchemyReadingSession(
            user_id=user_id,
            book_id=session_data.get('book_id'),
            current_location=session_data.get('current_location', '1:1:1'),  # Default to chapter:page:paragraph
            current_position_percent=session_data.get('current_position_percent', 0)
        )

        self.db.add(db_session)
        await self.db.commit()
        await self.db.refresh(db_session)

        # Convert to Pydantic model and return
        return self._convert_sqlalchemy_to_pydantic(db_session)

    async def get_user_sessions(self, user_id: str) -> List[PydanticReadingSession]:
        """Get all reading sessions for a user."""
        result = await self.db.execute(
            select(SQLAlchemyReadingSession).filter(SQLAlchemyReadingSession.user_id == user_id)
        )
        sessions = result.scalars().all()

        return [self._convert_sqlalchemy_to_pydantic(session) for session in sessions]

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

    async def update_session_location(self, session_id: str, location: str, position_percent: int) -> PydanticReadingSession:
        """Update the current reading location in a session."""
        try:
            # Validate UUID format
            uuid.UUID(session_id)
        except ValueError:
            raise ValueError(f"Invalid session ID: {session_id}")

        # Update the database
        stmt = (
            update(SQLAlchemyReadingSession)
            .where(SQLAlchemyReadingSession.id == session_id)
            .values(
                current_location=location,
                current_position_percent=position_percent,
                last_accessed_at=datetime.utcnow()
            )
        )

        await self.db.execute(stmt)
        await self.db.commit()

        # Return the updated session
        return await self.get_session_by_id(session_id)

    async def activate_session(self, session_id: str) -> bool:
        """Activate a reading session."""
        try:
            # Validate UUID format
            uuid.UUID(session_id)
        except ValueError:
            raise ValueError(f"Invalid session ID: {session_id}")

        stmt = (
            update(SQLAlchemyReadingSession)
            .where(SQLAlchemyReadingSession.id == session_id)
            .values(is_active=True)
        )

        result = await self.db.execute(stmt)
        await self.db.commit()

        return result.rowcount > 0

    async def deactivate_session(self, session_id: str) -> bool:
        """Deactivate a reading session."""
        try:
            # Validate UUID format
            uuid.UUID(session_id)
        except ValueError:
            raise ValueError(f"Invalid session ID: {session_id}")

        stmt = (
            update(SQLAlchemyReadingSession)
            .where(SQLAlchemyReadingSession.id == session_id)
            .values(is_active=False)
        )

        result = await self.db.execute(stmt)
        await self.db.commit()

        return result.rowcount > 0

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
            started_at=db_session.started_at,
            last_read_at=db_session.last_accessed_at or datetime.utcnow(),
            is_active=db_session.is_active,
            total_time_spent=0  # Not stored in DB, default to 0
        )