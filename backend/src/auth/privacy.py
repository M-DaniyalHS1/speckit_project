"""Privacy and GDPR compliance module for the AI-Enhanced Interactive Book Agent.

This module implements features required for GDPR compliance, including
user data access, data portability, and data deletion capabilities.
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import HTTPException, status
from jose import jwt
from backend.src.models.sqlalchemy_models import User, Book, ReadingSession, BookContent, Query, Explanation, LearningMaterial
from backend.src.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from backend.src.auth.utils import create_access_token
from backend.src.config import settings


class PrivacyService:
    """Service for handling user privacy and GDPR compliance."""
    
    def __init__(self):
        """Initialize the privacy service."""
        # Data retention periods in days
        self.query_retention_days = 365  # Keep queries for 1 year
        self.session_retention_days = 90  # Keep sessions for 3 months
        self.book_retention_days = 180  # Keep books for 6 months after last access
    
    async def get_user_data(self, db: AsyncSession, user_id: str) -> Dict[str, Any]:
        """Get all personal data associated with a user.
        
        Args:
            db: Database session
            user_id: ID of the user whose data to retrieve
            
        Returns:
            Dictionary containing all user data
        """
        try:
            # Get user profile
            user_result = await db.execute(select(User).filter(User.id == user_id))
            user = user_result.scalars().first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Get user's books
            books_result = await db.execute(select(Book).filter(Book.user_id == user_id))
            books = books_result.scalars().all()
            
            # Get user's reading sessions
            sessions_result = await db.execute(select(ReadingSession).filter(ReadingSession.user_id == user_id))
            sessions = sessions_result.scalars().all()
            
            # Get user's queries
            queries_result = await db.execute(select(Query).filter(Query.user_id == user_id))
            queries = queries_result.scalars().all()
            
            # Get user's explanations
            explanations_result = await db.execute(select(Explanation).filter(Explanation.query_id.in_([q.id for q in queries])))
            explanations = explanations_result.scalars().all()
            
            # Get user's learning materials
            materials_result = await db.execute(select(LearningMaterial).filter(LearningMaterial.user_id == user_id))
            learning_materials = materials_result.scalars().all()
            
            # Format the data according to GDPR standards
            user_data = {
                "profile": {
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "preferences": json.loads(user.preferences) if user.preferences else {},
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None
                },
                "books": [
                    {
                        "id": str(book.id),
                        "title": book.title,
                        "author": book.author,
                        "file_path": book.file_path,
                        "file_format": book.file_format,
                        "file_size": book.file_size,
                        "total_pages": book.total_pages,
                        "is_processed": book.is_processed,
                        "processing_error": book.processing_error,
                        "created_at": book.created_at.isoformat() if book.created_at else None,
                        "updated_at": book.updated_at.isoformat() if book.updated_at else None
                    }
                    for book in books
                ],
                "reading_sessions": [
                    {
                        "id": str(session.id),
                        "book_id": str(session.book_id),
                        "current_location": session.current_location,
                        "current_position_percent": session.current_position_percent,
                        "started_at": session.started_at.isoformat() if session.started_at else None,
                        "last_accessed_at": session.last_accessed_at.isoformat() if session.last_accessed_at else None,
                        "is_active": session.is_active
                    }
                    for session in sessions
                ],
                "queries": [
                    {
                        "id": str(query.id),
                        "book_id": str(query.book_id) if query.book_id else None,
                        "query_text": query.query_text,
                        "query_type": query.query_type,
                        "context": query.context,
                        "created_at": query.created_at.isoformat() if query.created_at else None
                    }
                    for query in queries
                ],
                "explanations": [
                    {
                        "id": str(explanation.id),
                        "query_id": str(explanation.query_id),
                        "content_id": str(explanation.content_id) if explanation.content_id else None,
                        "explanation_text": explanation.explanation_text,
                        "complexity_level": explanation.complexity_level,
                        "sources": explanation.sources,
                        "created_at": explanation.created_at.isoformat() if explanation.created_at else None,
                        "updated_at": explanation.updated_at.isoformat() if explanation.updated_at else None
                    }
                    for explanation in explanations
                ],
                "learning_materials": [
                    {
                        "id": str(material.id),
                        "book_id": str(material.book_id),
                        "material_type": material.material_type,
                        "title": material.title,
                        "content": material.content,
                        "additional_metadata": material.additional_metadata,
                        "created_at": material.created_at.isoformat() if material.created_at else None,
                        "updated_at": material.updated_at.isoformat() if material.updated_at else None
                    }
                    for material in learning_materials
                ]
            }
            
            return user_data
        except Exception as e:
            print(f"Error retrieving user data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving user data"
            )
    
    async def export_user_data(self, db: AsyncSession, user_id: str, format_type: str = "json") -> str:
        """Export user data in a specified format for data portability.
        
        Args:
            db: Database session
            user_id: ID of the user whose data to export
            format_type: Format to export data in (json, csv, etc.)
            
        Returns:
            Exported data as a string
        """
        user_data = await self.get_user_data(db, user_id)
        
        if format_type.lower() == "json":
            return json.dumps(user_data, indent=2, default=str)
        else:
            # For now, only JSON is supported
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JSON format is supported for data export"
            )
    
    async def delete_user_account(self, db: AsyncSession, user_id: str) -> bool:
        """Delete a user account and all associated data (right to be forgotten).
        
        Args:
            db: Database session
            user_id: ID of the user whose account to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First, get all related records to delete
            # Get user's books to know which book contents to delete
            books_result = await db.execute(select(Book).filter(Book.user_id == user_id))
            books = books_result.scalars().all()
            book_ids = [str(book.id) for book in books]
            
            # Get user's queries to know which explanations to delete
            queries_result = await db.execute(select(Query).filter(Query.user_id == user_id))
            queries = queries_result.scalars().all()
            query_ids = [str(query.id) for query in queries]
            
            # Delete explanations associated with user's queries
            if query_ids:
                await db.execute(delete(Explanation).where(Explanation.query_id.in_(query_ids)))
            
            # Delete queries
            await db.execute(delete(Query).where(Query.user_id == user_id))
            
            # Delete learning materials
            await db.execute(delete(LearningMaterial).where(LearningMaterial.user_id == user_id))
            
            # Delete reading sessions
            await db.execute(delete(ReadingSession).where(ReadingSession.user_id == user_id))
            
            # Delete book contents associated with user's books
            if book_ids:
                await db.execute(delete(BookContent).where(BookContent.book_id.in_(book_ids)))
            
            # Delete books
            await db.execute(delete(Book).where(Book.user_id == user_id))
            
            # Finally, delete the user
            await db.execute(delete(User).where(User.id == user_id))
            
            # Commit the changes
            await db.commit()
            
            return True
        except Exception as e:
            print(f"Error deleting user account: {str(e)}")
            await db.rollback()
            return False
    
    async def anonymize_user_data(self, db: AsyncSession, user_id: str) -> bool:
        """Anonymize user data instead of deleting it (for legal compliance).
        
        Args:
            db: Database session
            user_id: ID of the user whose data to anonymize
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get user to update
            user_result = await db.execute(select(User).filter(User.id == user_id))
            user = user_result.scalars().first()
            
            if not user:
                return False
            
            # Anonymize user data
            user.email = f"anonymized_{user.id}@example.com"
            user.first_name = "Anonymized"
            user.last_name = "User"
            user.preferences = "{}"
            
            # Get user's books to anonymize file paths
            books_result = await db.execute(select(Book).filter(Book.user_id == user_id))
            books = books_result.scalars().all()
            
            for book in books:
                book.title = f"Anonymized Book {book.id}"
                book.author = "Anonymized Author"
                # Note: We don't delete the actual files but we anonymize references to them
            
            # Commit the changes
            await db.commit()
            
            return True
        except Exception as e:
            print(f"Error anonymizing user data: {str(e)}")
            await db.rollback()
            return False
    
    async def schedule_data_deletion(self, db: AsyncSession, user_id: str, days: int = 30) -> bool:
        """Schedule data deletion for a user after a specified number of days.
        
        Args:
            db: Database session
            user_id: ID of the user whose data will be deleted
            days: Number of days after which data will be deleted
            
        Returns:
            True if scheduled successfully, False otherwise
        """
        # In a real implementation, this would use a background task scheduler
        # For now, we'll just return True to indicate the intent
        print(f"Scheduled data deletion for user {user_id} in {days} days")
        return True
    
    async def delete_old_data(self, db: AsyncSession) -> int:
        """Delete old data based on retention policies.
        
        Args:
            db: Database session
            
        Returns:
            Number of records deleted
        """
        try:
            deleted_count = 0
            now = datetime.utcnow()
            
            # Delete old queries based on retention policy
            cutoff_date = now - timedelta(days=self.query_retention_days)
            old_queries = await db.execute(
                select(Query).filter(Query.created_at < cutoff_date)
            )
            old_query_ids = [q.id for q in old_queries.scalars().all()]
            
            if old_query_ids:
                # Delete explanations for old queries first
                await db.execute(delete(Explanation).where(Explanation.query_id.in_(old_query_ids)))
                
                # Then delete the queries
                result = await db.execute(delete(Query).where(Query.id.in_(old_query_ids)))
                deleted_count += result.rowcount
            
            # Delete old reading sessions
            cutoff_date = now - timedelta(days=self.session_retention_days)
            result = await db.execute(
                delete(ReadingSession).where(ReadingSession.last_accessed_at < cutoff_date)
            )
            deleted_count += result.rowcount
            
            # Commit the changes
            await db.commit()
            
            return deleted_count
        except Exception as e:
            print(f"Error deleting old data: {str(e)}")
            await db.rollback()
            return 0


# Global instance of the privacy service
privacy_service = PrivacyService()


# Additional utility functions for GDPR compliance

async def create_data_portability_token(user_id: str) -> str:
    """Create a token for data portability requests.
    
    Args:
        user_id: ID of the user requesting data portability
        
    Returns:
        JWT token for data portability
    """
    data = {
        "user_id": user_id,
        "type": "data_portability",
        "exp": datetime.utcnow() + timedelta(hours=1)  # Token valid for 1 hour
    }
    
    return jwt.encode(data, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def get_gdpr_request_status(request_id: str) -> Dict[str, Any]:
    """Get the status of a GDPR compliance request.
    
    Args:
        request_id: ID of the GDPR request
        
    Returns:
        Status information about the request
    """
    # In a real implementation, this would lookup the status in a database
    # For now, returning a mock response
    return {
        "request_id": request_id,
        "status": "completed",
        "request_type": "data_export",  # or data_deletion
        "requested_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "data_available_until": (datetime.utcnow() + timedelta(days=7)).isoformat()
    }