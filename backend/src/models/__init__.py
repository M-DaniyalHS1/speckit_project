"""Models package for AI-Enhanced Interactive Book Agent."""
from .user import User as PydanticUser
from .book import Book as PydanticBook
from .reading_session import ReadingSession as PydanticReadingSession
from .book_content import BookContent as PydanticBookContent
from .query import Query as PydanticQuery
from .explanation import Explanation as PydanticExplanation
from .learning_material import LearningMaterial as PydanticLearningMaterial
from .sqlalchemy_models import User as SQLAlchemyUser

__all__ = [
    "PydanticUser",
    "PydanticBook",
    "PydanticReadingSession",
    "PydanticBookContent",
    "PydanticQuery",
    "PydanticExplanation",
    "PydanticLearningMaterial",
    "SQLAlchemyUser",
]