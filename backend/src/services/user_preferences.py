"""User preference handling service for the AI-Enhanced Interactive Book Agent.

This module provides functionality to manage user preferences, particularly
for controlling explanation depth and other AI-generated content settings.
"""
from typing import Dict, Any, Optional, Literal, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
import uuid
from datetime import datetime

from backend.src.models.sqlalchemy_models import User, Book
from backend.src.models.user import User as PydanticUser
from backend.src.config import settings


# Define types for explanation preferences
ExplanationDepth = Literal["simple", "detailed", "technical", "adaptive"]
ReadingPreference = Literal["fast", "thorough", "review", "learning"]
DifficultyLevel = Literal["beginner", "intermediate", "advanced", "expert"]


class UserPreferenceService:
    """Service for managing user preferences, particularly for AI-generated content customization."""

    def __init__(self, db: AsyncSession):
        """Initialize the user preference service with a database session."""
        self.db = db

    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get all preferences for a specific user.

        Args:
            user_id: ID of the user to retrieve preferences for

        Returns:
            Dictionary containing all user preferences
        """
        try:
            # Verify user exists
            user_result = await self.db.execute(
                select(User).filter(User.id == user_id)
            )
            user = user_result.scalars().first()

            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            # Get user preferences from the database
            # In a real implementation, these might be stored in a separate preferences table
            # For now, we'll provide a default implementation with common preferences
            user_preferences = {
                "user_id": user_id,
                "explanation_preferences": {
                    "default_depth": getattr(user, 'default_explanation_depth', 'detailed'),
                    "technical_jargon_tolerance": getattr(user, 'technical_tolerance', 0.5),  # 0-1 scale
                    "examples_preference": getattr(user, 'examples_preference', True),  # Want examples or not
                    "previous_topics_reference": getattr(user, 'reference_previous', True),  # Reference previous topics
                },
                "reading_preferences": {
                    "preferred_speed": getattr(user, 'reading_speed', 'thorough'),
                    "distraction_tolerance": getattr(user, 'distraction_tolerance', 0.7),  # 0-1 scale
                    "note_taking_frequency": getattr(user, 'note_frequency', 'moderate'),  # never, occasional, frequent, always
                },
                "content_preferences": {
                    "difficulty_level": getattr(user, 'difficulty_level', 'intermediate'),
                    "subject_interests": getattr(user, 'subject_interests', []),  # List of subjects
                    "avoid_topics": getattr(user, 'avoid_topics', []),  # Topics to avoid
                    "learning_goals": getattr(user, 'learning_goals', []),  # Learning objectives
                },
                "ai_interaction_preferences": {
                    "question_frequency": getattr(user, 'question_frequency', 'moderate'),  # none, low, moderate, high, adaptive
                    "feedback_frequency": getattr(user, 'feedback_frequency', 'moderate'),  # How often to ask for feedback
                    "progress_tracking": getattr(user, 'progress_tracking', True),  # Track learning progress
                },
                "updated_at": getattr(user, 'preferences_updated_at', datetime.utcnow()).isoformat()
            }

            return user_preferences

        except SQLAlchemyError as e:
            raise ValueError(f"Database error while retrieving user preferences: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error retrieving user preferences: {str(e)}")

    async def set_explanation_depth(
        self, 
        user_id: str, 
        depth: ExplanationDepth,
        book_id: Optional[str] = None
    ) -> bool:
        """Set the explanation depth preference for a user.

        Args:
            user_id: ID of the user
            depth: Desired explanation depth (simple, detailed, technical, adaptive)
            book_id: Optional book ID to set book-specific preference

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate user exists
            user_result = await self.db.execute(
                select(User).filter(User.id == user_id)
            )
            user = user_result.scalars().first()

            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            # In a real implementation, we would save this to a preferences table
            # For this example, we'll simulate by updating a field on the user model
            # Though in practice, preferences might be stored separately
            
            # Determine preference key based on whether book-specific
            if book_id:
                # Validate book exists and belongs to user
                book_result = await self.db.execute(
                    select(Book).filter(Book.id == book_id, Book.user_id == user_id)
                )
                book = book_result.scalars().first()
                
                if not book:
                    raise ValueError(f"Book with ID {book_id} not found or access denied")
                
                # In a real system, we'd store book-specific preferences in a separate table
                # For now, we'll note it as a book-specific setting
                preference_key = f"explanation_depth_{book_id}"
            else:
                preference_key = "default_explanation_depth"
            
            # Update the user's preference in their preferences JSON field
            # This is a simplified approach - a real implementation would use a dedicated preferences table
            if not hasattr(user, 'preferences') or user.preferences is None:
                user.preferences = {}
            
            import json
            current_prefs = json.loads(user.preferences) if isinstance(user.preferences, str) else user.preferences
            current_prefs[preference_key] = depth
            user.preferences = json.dumps(current_prefs)
            
            # Update timestamp
            user.updated_at = datetime.utcnow()
            
            # Commit changes
            await self.db.commit()
            await self.db.refresh(user)
            
            return True

        except SQLAlchemyError as e:
            await self.db.rollback()
            raise ValueError(f"Database error while setting explanation depth: {str(e)}")
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Error setting explanation depth: {str(e)}")

    async def get_explanation_depth(
        self, 
        user_id: str, 
        book_id: Optional[str] = None
    ) -> ExplanationDepth:
        """Get the explanation depth preference for a user.

        Args:
            user_id: ID of the user
            book_id: Optional book ID to get book-specific preference

        Returns:
            User's preferred explanation depth
        """
        try:
            # Validate user exists
            user_result = await self.db.execute(
                select(User).filter(User.id == user_id)
            )
            user = user_result.scalars().first()

            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            # Determine which preference to retrieve
            if book_id:
                # Check if there's a book-specific preference
                import json
                current_prefs = json.loads(user.preferences) if isinstance(user.preferences, str) and user.preferences else {}
                book_specific_key = f"explanation_depth_{book_id}"
                
                if book_specific_key in current_prefs:
                    depth = current_prefs[book_specific_key]
                    if depth in ["simple", "detailed", "technical", "adaptive"]:
                        return depth  # type: ignore

            # Fall back to default preference
            import json
            current_prefs = json.loads(user.preferences) if isinstance(user.preferences, str) and user.preferences else {}
            default_depth = current_prefs.get("default_explanation_depth", "detailed")
            
            if default_depth in ["simple", "detailed", "technical", "adaptive"]:
                return default_depth  # type: ignore
            else:
                return "detailed"  # Default fallback

        except Exception as e:
            # In case of any error, return a default value
            return "detailed"

    async def set_content_difficulty_preference(
        self, 
        user_id: str, 
        difficulty: DifficultyLevel,
        subject: Optional[str] = None
    ) -> bool:
        """Set the content difficulty preference for a user.

        Args:
            user_id: ID of the user
            difficulty: Desired difficulty level (beginner, intermediate, advanced, expert)
            subject: Optional subject to set subject-specific preference

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate user exists
            user_result = await self.db.execute(
                select(User).filter(User.id == user_id)
            )
            user = user_result.scalars().first()

            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            # Determine preference key based on whether subject-specific
            if subject:
                preference_key = f"difficulty_{subject}"
            else:
                preference_key = "default_difficulty"

            # Update the user's preference in their preferences JSON field
            import json
            current_prefs = json.loads(user.preferences) if isinstance(user.preferences, str) else {}
            current_prefs[preference_key] = difficulty
            user.preferences = json.dumps(current_prefs)

            # Update timestamp
            user.updated_at = datetime.utcnow()

            # Commit changes
            await self.db.commit()
            await self.db.refresh(user)

            return True

        except SQLAlchemyError as e:
            await self.db.rollback()
            raise ValueError(f"Database error while setting difficulty preference: {str(e)}")
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Error setting difficulty preference: {str(e)}")

    async def get_content_difficulty_preference(
        self, 
        user_id: str, 
        subject: Optional[str] = None
    ) -> DifficultyLevel:
        """Get the content difficulty preference for a user.

        Args:
            user_id: ID of the user
            subject: Optional subject to get subject-specific preference

        Returns:
            User's preferred difficulty level
        """
        try:
            # Validate user exists
            user_result = await self.db.execute(
                select(User).filter(User.id == user_id)
            )
            user = user_result.scalars().first()

            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            # Determine which preference to retrieve
            import json
            current_prefs = json.loads(user.preferences) if isinstance(user.preferences, str) and user.preferences else {}
            
            if subject and f"difficulty_{subject}" in current_prefs:
                difficulty = current_prefs[f"difficulty_{subject}"]
                if difficulty in ["beginner", "intermediate", "advanced", "expert"]:
                    return difficulty  # type: ignore

            # Fall back to default preference
            default_difficulty = current_prefs.get("default_difficulty", "intermediate")

            if default_difficulty in ["beginner", "intermediate", "advanced", "expert"]:
                return default_difficulty  # type: ignore
            else:
                return "intermediate"  # Default fallback

        except Exception as e:
            # In case of any error, return a default value
            return "intermediate"

    async def set_reading_speed_preference(
        self,
        user_id: str,
        speed: ReadingPreference
    ) -> bool:
        """Set the preferred reading speed for a user.

        Args:
            user_id: ID of the user
            speed: Preferred reading speed (fast, thorough, review, learning)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate user exists
            user_result = await self.db.execute(
                select(User).filter(User.id == user_id)
            )
            user = user_result.scalars().first()

            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            # Update the user's preference in their preferences JSON field
            import json
            current_prefs = json.loads(user.preferences) if isinstance(user.preferences, str) else {}
            current_prefs["reading_speed"] = speed
            user.preferences = json.dumps(current_prefs)

            # Update timestamp
            user.updated_at = datetime.utcnow()

            # Commit changes
            await self.db.commit()
            await self.db.refresh(user)

            return True

        except SQLAlchemyError as e:
            await self.db.rollback()
            raise ValueError(f"Database error while setting reading speed preference: {str(e)}")
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Error setting reading speed preference: {str(e)}")

    async def update_user_subject_interests(
        self,
        user_id: str,
        subjects: List[str],
        operation: Literal["set", "add", "remove"] = "set"
    ) -> bool:
        """Update the user's subject interests.

        Args:
            user_id: ID of the user
            subjects: List of subjects to update interest in
            operation: Operation to perform - set (replace), add, or remove

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate user exists
            user_result = await self.db.execute(
                select(User).filter(User.id == user_id)
            )
            user = user_result.scalars().first()

            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            import json
            current_prefs = json.loads(user.preferences) if isinstance(user.preferences, str) else {}

            if operation == "set":
                # Replace all subject interests
                current_prefs["subject_interests"] = subjects
            elif operation == "add":
                # Add to existing subject interests
                existing_interests = current_prefs.get("subject_interests", [])
                for subject in subjects:
                    if subject not in existing_interests:
                        existing_interests.append(subject)
                current_prefs["subject_interests"] = existing_interests
            elif operation == "remove":
                # Remove specific subjects from interests
                existing_interests = current_prefs.get("subject_interests", [])
                current_prefs["subject_interests"] = [subj for subj in existing_interests if subj not in subjects]

            user.preferences = json.dumps(current_prefs)

            # Update timestamp
            user.updated_at = datetime.utcnow()

            # Commit changes
            await self.db.commit()
            await self.db.refresh(user)

            return True

        except SQLAlchemyError as e:
            await self.db.rollback()
            raise ValueError(f"Database error while updating subject interests: {str(e)}")
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Error updating subject interests: {str(e)}")

    async def get_user_explanation_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get explanation-specific preferences for a user.

        Args:
            user_id: ID of the user

        Returns:
            Dictionary containing explanation-related preferences
        """
        try:
            # Get all user preferences
            all_prefs = await self.get_user_preferences(user_id)

            # Extract just the explanation preferences
            explanation_prefs = all_prefs.get("explanation_preferences", {})

            return explanation_prefs

        except Exception as e:
            # In case of any error, return default values
            return {
                "default_depth": "detailed",
                "technical_jargon_tolerance": 0.5,
                "examples_preference": True,
                "previous_topics_reference": True,
            }

    async def reset_user_preferences(self, user_id: str, preference_type: Optional[str] = None) -> bool:
        """Reset user preferences to default values.

        Args:
            user_id: ID of the user
            preference_type: Optional specific type of preferences to reset (None to reset all)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate user exists
            user_result = await self.db.execute(
                select(User).filter(User.id == user_id)
            )
            user = user_result.scalars().first()

            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            import json
            current_prefs = json.loads(user.preferences) if isinstance(user.preferences, str) else {}

            if preference_type:
                # Reset only the specified preference type
                if preference_type == "explanation":
                    current_prefs.pop("default_explanation_depth", None)
                    current_prefs.pop("technical_tolerance", None)
                    current_prefs.pop("examples_preference", None)
                    current_prefs.pop("reference_previous", None)
                elif preference_type == "difficulty":
                    current_prefs.pop("default_difficulty", None)
                elif preference_type == "reading":
                    current_prefs.pop("reading_speed", None)
                else:
                    # Unknown preference type, return False
                    return False
            else:
                # Reset all preferences to default
                current_prefs = {}

            user.preferences = json.dumps(current_prefs)

            # Update timestamp
            user.updated_at = datetime.utcnow()

            # Commit changes
            await self.db.commit()
            await self.db.refresh(user)

            return True

        except SQLAlchemyError as e:
            await self.db.rollback()
            raise ValueError(f"Database error while resetting preferences: {str(e)}")
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Error resetting preferences: {str(e)}")


# Global instance of the user preference service
user_preference_service = UserPreferenceService(None)  # This will be replaced when db session is provided


def init_user_preference_service(db_session: AsyncSession) -> UserPreferenceService:
    """Initialize the user preference service with a database session.

    Args:
        db_session: Async database session

    Returns:
        Initialized UserPreferenceService
    """
    global user_preference_service
    user_preference_service = UserPreferenceService(db_session)
    return user_preference_service