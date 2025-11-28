"""Service layer for explanation operations in AI-Enhanced Interactive Book Agent."""
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from backend.src.models.sqlalchemy_models import Explanation as SQLAlchemyExplanation, BookContent, Query as SQLAlchemyQuery
from backend.src.models.explanation import Explanation as PydanticExplanation
from backend.src.ai.explanation_generator import ExplanationGenerator


class ExplanationService:
    """Service class for handling explanation operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the service with a database session."""
        self.db = db
        self.explanation_generator = ExplanationGenerator()

    async def create_explanation(
        self, 
        user_id: str, 
        book_id: str, 
        content_id: str, 
        query_text: str, 
        complexity_level: str = "simple"
    ) -> PydanticExplanation:
        """Create an explanation for specific book content."""
        # First create a query record
        query = SQLAlchemyQuery(
            user_id=user_id,
            book_id=book_id,
            query_text=query_text,
            query_type="explanation"
        )
        self.db.add(query)
        await self.db.commit()
        await self.db.refresh(query)

        # Generate explanation using AI
        content_result = await self.db.execute(
            select(BookContent).filter(BookContent.id == content_id)
        )
        content = content_result.scalars().first()
        
        if not content:
            raise ValueError(f"Content with id {content_id} not found")
        
        explanation_text = await self.explanation_generator.generate_explanation(
            content.content,
            query_text,
            complexity_level
        )

        # Create the explanation record
        db_explanation = SQLAlchemyExplanation(
            query_id=query.id,
            content_id=content_id,
            explanation_text=explanation_text,
            complexity_level=complexity_level,
            sources=f"[{content_id}]"  # In a real implementation, this would include more sources
        )
        
        self.db.add(db_explanation)
        await self.db.commit()
        await self.db.refresh(db_explanation)
        
        # Convert to Pydantic model and return
        return self._convert_sqlalchemy_to_pydantic(db_explanation)

    async def get_explanation_by_id(self, explanation_id: str) -> Optional[PydanticExplanation]:
        """Get a specific explanation by its ID."""
        try:
            # Validate UUID format
            uuid.UUID(explanation_id)
        except ValueError:
            return None
            
        result = await self.db.execute(
            select(SQLAlchemyExplanation).filter(SQLAlchemyExplanation.id == explanation_id)
        )
        explanation = result.scalars().first()
        
        if explanation:
            return self._convert_sqlalchemy_to_pydantic(explanation)
        return None

    async def generate_explanation(
        self,
        user_id: str,
        book_id: str,
        content_id: str,
        query_text: str,
        complexity_level: str = "simple"
    ) -> PydanticExplanation:
        """Generate an explanation for specific book content using AI."""
        # This is essentially the same as create_explanation but with AI generation
        return await self.create_explanation(
            user_id, book_id, content_id, query_text, complexity_level
        )

    def _convert_sqlalchemy_to_pydantic(self, db_explanation: SQLAlchemyExplanation) -> PydanticExplanation:
        """
        Convert SQLAlchemy Explanation model to Pydantic Explanation model.
        """
        return PydanticExplanation(
            id=str(db_explanation.id),
            query_id=str(db_explanation.query_id),
            content_id=str(db_explanation.content_id) if db_explanation.content_id else None,
            explanation_text=db_explanation.explanation_text,
            complexity_level=db_explanation.complexity_level,
            sources=db_explanation.sources,
            created_at=db_explanation.created_at,
            updated_at=db_explanation.updated_at
        )