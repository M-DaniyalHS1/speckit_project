"""Service layer for summarization operations in AI-Enhanced Interactive Book Agent."""
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from backend.src.models.sqlalchemy_models import LearningMaterial as SQLAlchemyLearningMaterial, BookContent, Query as SQLAlchemyQuery
from backend.src.models.learning_material import LearningMaterial as PydanticLearningMaterial
from backend.src.ai.summarization_generator import SummarizationGenerator


class SummarizationService:
    """Service class for handling summarization operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the service with a database session."""
        self.db = db
        self.summarization_generator = SummarizationGenerator()

    async def create_summary(
        self, 
        user_id: str, 
        book_id: str, 
        content_id: str, 
        title: str, 
        content: str
    ) -> PydanticLearningMaterial:
        """Create a summary for specific book content."""
        # Create the learning material record as a summary
        db_summary = SQLAlchemyLearningMaterial(
            user_id=user_id,
            book_id=book_id,
            material_type="summary",
            title=title,
            content=content,
            metadata='{}'  # In a real implementation, this could store additional metadata
        )
        
        self.db.add(db_summary)
        await self.db.commit()
        await self.db.refresh(db_summary)
        
        # Convert to Pydantic model and return
        return self._convert_sqlalchemy_to_pydantic(db_summary)

    async def generate_summary(
        self,
        user_id: str,
        book_id: str,
        content_id: str,
        summary_type: str = "section"
    ) -> PydanticLearningMaterial:
        """Generate a summary for specific book content using AI."""
        # Get the content to summarize
        content_result = await self.db.execute(
            select(BookContent).filter(BookContent.id == content_id)
        )
        content = content_result.scalars().first()
        
        if not content:
            raise ValueError(f"Content with id {content_id} not found")
        
        # Generate summary based on summary type
        if summary_type == "section":
            summary_text = await self.summarization_generator.generate_section_summary(
                content.content
            )
            title = f"Summary: {content.section_title or 'Section'}"
        elif summary_type == "chapter":
            # In a real implementation, we'd gather all sections of the chapter
            summary_text = await self.summarization_generator.generate_section_summary(
                content.content
            )
            title = f"Chapter Summary: {content.chapter or 'Chapter'}"
        elif summary_type == "book":
            # In a real implementation, we'd gather all content of the book
            summary_text = await self.summarization_generator.generate_section_summary(
                content.content
            )
            title = "Book Summary"
        else:
            summary_text = await self.summarization_generator.generate_section_summary(
                content.content
            )
            title = f"Summary: {content.section_title or 'Content'}"
        
        # Create the summary record
        db_summary = SQLAlchemyLearningMaterial(
            user_id=user_id,
            book_id=book_id,
            material_type="summary",
            title=title,
            content=summary_text,
            additional_metadata=f'{{"content_id": "{content_id}", "summary_type": "{summary_type}"}}'
        )
        
        self.db.add(db_summary)
        await self.db.commit()
        await self.db.refresh(db_summary)
        
        return self._convert_sqlalchemy_to_pydantic(db_summary)

    def _convert_sqlalchemy_to_pydantic(self, db_summary: SQLAlchemyLearningMaterial) -> PydanticLearningMaterial:
        """
        Convert SQLAlchemy LearningMaterial model to Pydantic LearningMaterial model.
        """
        return PydanticLearningMaterial(
            id=str(db_summary.id),
            user_id=str(db_summary.user_id),
            book_id=str(db_summary.book_id),
            material_type=db_summary.material_type,
            title=db_summary.title,
            content=db_summary.content,
            metadata=db_summary.additional_metadata,
            created_at=db_summary.created_at,
            updated_at=db_summary.updated_at
        )