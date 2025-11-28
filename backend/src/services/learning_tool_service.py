"""Service layer for learning tool operations in AI-Enhanced Interactive Book Agent."""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from backend.src.models.sqlalchemy_models import LearningMaterial as SQLAlchemyLearningMaterial, BookContent, Book
from backend.src.models.learning_material import LearningMaterial as PydanticLearningMaterial
from backend.src.ai.learning_material_generator import LearningMaterialGenerator


class LearningToolService:
    """Service class for handling learning tool operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the service with a database session."""
        self.db = db
        self.material_generator = LearningMaterialGenerator()

    async def create_learning_material(
        self,
        user_id: str,
        book_id: str,
        material_type: str,
        title: str,
        content: str,
        metadata: dict = None
    ) -> PydanticLearningMaterial:
        """Create a new learning material."""
        db_material = SQLAlchemyLearningMaterial(
            user_id=user_id,
            book_id=book_id,
            material_type=material_type,
            title=title,
            content=content,
            additional_metadata=str(metadata) if metadata else '{}'
        )
        
        self.db.add(db_material)
        await self.db.commit()
        await self.db.refresh(db_material)
        
        return self._convert_sqlalchemy_to_pydantic(db_material)

    async def get_learning_materials_for_book(self, book_id: str) -> List[PydanticLearningMaterial]:
        """Get all learning materials for a specific book."""
        result = await self.db.execute(
            select(SQLAlchemyLearningMaterial)
            .filter(SQLAlchemyLearningMaterial.book_id == book_id)
        )
        materials = result.scalars().all()
        
        return [self._convert_sqlalchemy_to_pydantic(material) for material in materials]

    async def get_learning_material_by_id(self, material_id: str) -> Optional[PydanticLearningMaterial]:
        """Get a specific learning material by its ID."""
        try:
            # Validate UUID format
            uuid.UUID(material_id)
        except ValueError:
            return None
            
        result = await self.db.execute(
            select(SQLAlchemyLearningMaterial).filter(SQLAlchemyLearningMaterial.id == material_id)
        )
        material = result.scalars().first()
        
        if material:
            return self._convert_sqlalchemy_to_pydantic(material)
        return None

    async def generate_quiz(
        self,
        user_id: str,
        book_id: str,
        content_id: str = None,
        num_questions: int = 5
    ) -> List[PydanticLearningMaterial]:
        """Generate quiz questions for specific book content using AI."""
        content_text = ""
        
        if content_id:
            # Get specific content to generate quiz from
            content_result = await self.db.execute(
                select(BookContent).filter(BookContent.id == content_id)
            )
            content = content_result.scalars().first()
            if content:
                content_text = content.content
        else:
            # Get content for the entire book (first few chunks for example)
            book_result = await self.db.execute(
                select(Book).filter(Book.id == book_id)
            )
            book = book_result.scalars().first()
            if book:
                # In a real implementation, we'd gather content from the entire book
                # For now, we'll just get the first content chunk
                content_result = await self.db.execute(
                    select(BookContent)
                    .filter(BookContent.book_id == book_id)
                    .limit(1)
                )
                content = content_result.scalars().first()
                if content:
                    content_text = content.content
        
        # Generate quiz questions using AI
        quiz_questions = await self.material_generator.generate_quiz(
            content_text,
            num_questions
        )
        
        # Create learning material records for each question
        created_materials = []
        for i, question in enumerate(quiz_questions):
            material = SQLAlchemyLearningMaterial(
                user_id=user_id,
                book_id=book_id,
                material_type="quiz",
                title=f"Quiz Question {i+1}",
                content=question,
                additional_metadata=f'{{"question_number": {i+1}, "content_id": "{content_id}"}}'
            )
            
            self.db.add(material)
            await self.db.commit()
            await self.db.refresh(material)
            
            created_materials.append(self._convert_sqlalchemy_to_pydantic(material))
        
        return created_materials

    async def generate_flashcards(
        self,
        user_id: str,
        book_id: str,
        content_id: str = None
    ) -> List[PydanticLearningMaterial]:
        """Generate flashcards for specific book content using AI."""
        content_text = ""
        
        if content_id:
            # Get specific content to generate flashcards from
            content_result = await self.db.execute(
                select(BookContent).filter(BookContent.id == content_id)
            )
            content = content_result.scalars().first()
            if content:
                content_text = content.content
        else:
            # Get content for the entire book (first few chunks for example)
            book_result = await self.db.execute(
                select(Book).filter(Book.id == book_id)
            )
            book = book_result.scalars().first()
            if book:
                # In a real implementation, we'd gather content from the entire book
                # For now, we'll just get the first content chunk
                content_result = await self.db.execute(
                    select(BookContent)
                    .filter(BookContent.book_id == book_id)
                    .limit(1)
                )
                content = content_result.scalars().first()
                if content:
                    content_text = content.content
        
        # Generate flashcards using AI
        flashcards = await self.material_generator.generate_flashcards(content_text)
        
        # Create learning material records for each flashcard
        created_materials = []
        for i, card in enumerate(flashcards):
            material = SQLAlchemyLearningMaterial(
                user_id=user_id,
                book_id=book_id,
                material_type="flashcard",
                title=f"Flashcard {i+1}",
                content=card,
                additional_metadata=f'{{"card_number": {i+1}, "content_id": "{content_id}"}}'
            )
            
            self.db.add(material)
            await self.db.commit()
            await self.db.refresh(material)
            
            created_materials.append(self._convert_sqlalchemy_to_pydantic(material))
        
        return created_materials

    def _convert_sqlalchemy_to_pydantic(self, db_material: SQLAlchemyLearningMaterial) -> PydanticLearningMaterial:
        """
        Convert SQLAlchemy LearningMaterial model to Pydantic LearningMaterial model.
        """
        return PydanticLearningMaterial(
            id=str(db_material.id),
            user_id=str(db_material.user_id),
            book_id=str(db_material.book_id),
            material_type=db_material.material_type,
            title=db_material.title,
            content=db_material.content,
            metadata=db_material.additional_metadata,
            created_at=db_material.created_at,
            updated_at=db_material.updated_at
        )