"""Flashcard generation service for the AI-Enhanced Interactive Book Agent."""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from backend.src.models.sqlalchemy_models import Book, BookContent, LearningMaterial
from backend.src.models.learning_material import LearningMaterial as PydanticLearningMaterial
from backend.src.ai.question_generator import QuestionGenerator
from backend.src.ai.explanation_generator import ExplanationGenerator


class FlashcardService:
    """Service for generating flashcards from book content using AI."""

    def __init__(self, db: AsyncSession):
        """Initialize the flashcard service with a database session."""
        self.db = db
        self.question_generator = QuestionGenerator()
        self.explanation_generator = ExplanationGenerator()

    async def generate_flashcards(
        self,
        user_id: str,
        book_id: str,
        content_id: Optional[str] = None,
        num_flashcards: int = 5
    ) -> List[Dict[str, str]]:
        """
        Generate flashcards for specific book content using AI.
        
        Args:
            user_id: ID of the user requesting flashcards
            book_id: ID of the book to generate flashcards from
            content_id: Optional specific content ID to focus on (if None, uses whole book)
            num_flashcards: Number of flashcards to generate
        
        Returns:
            List of flashcards with question and answer
        """
        # Verify user has access to the book
        book_result = await self.db.execute(
            select(Book).filter(Book.id == book_id, Book.user_id == user_id)
        )
        book = book_result.scalars().first()

        if not book:
            raise ValueError("Book not found or access denied")

        # Get content to generate flashcards from
        if content_id:
            content_result = await self.db.execute(
                select(BookContent).filter(BookContent.id == content_id, BookContent.book_id == book_id)
            )
            book_content = content_result.scalars().first()
            
            if not book_content:
                raise ValueError("Content not found")
                
            content = [book_content]
        else:
            # Get all content for the book
            content_result = await self.db.execute(
                select(BookContent).filter(BookContent.book_id == book_id)
            )
            content = content_result.scalars().all()
        
        if not content:
            raise ValueError("No content available for flashcard generation")
            
        # Combine content for context
        all_content_text = " ".join([c.content for c in content])

        # Generate flashcards using AI
        flashcards = []

        # Generate question-answer pairs
        qa_pairs = await self.question_generator.generate_questions_and_answers(
            content=all_content_text,
            count=num_flashcards
        )

        for pair in qa_pairs:
            flashcard = {
                "question": pair["question"],
                "answer": pair["answer"],
                "explanation": pair.get("explanation", ""),
                "difficulty": pair.get("difficulty", "medium")
            }
            flashcards.append(flashcard)

        # Create learning materials for each flashcard
        for i, flashcard in enumerate(flashcards):
            learning_material = LearningMaterial(
                user_id=user_id,
                book_id=book_id,
                material_type="flashcard",
                title=f"Flashcard {i+1}: {flashcard['question'][:50]}...",
                content=f"Q: {flashcard['question']}\nA: {flashcard['answer']}\nExplanation: {flashcard['explanation']}",
                additional_metadata={
                    "question": flashcard["question"],
                    "answer": flashcard["answer"],
                    "explanation": flashcard["explanation"],
                    "difficulty": flashcard["difficulty"]
                }
            )
            self.db.add(learning_material)

        await self.db.commit()
        
        return flashcards

    async def get_flashcards_by_book(
        self,
        user_id: str,
        book_id: str
    ) -> List[PydanticLearningMaterial]:
        """
        Get all flashcard learning materials for a book.
        
        Args:
            user_id: ID of the user requesting flashcards
            book_id: ID of the book to get flashcards for
        
        Returns:
            List of flashcard learning materials
        """
        # Verify user has access to the book
        book_result = await self.db.execute(
            select(Book).filter(Book.id == book_id, Book.user_id == user_id)
        )
        book = book_result.scalars().first()

        if not book:
            raise ValueError("Book not found or access denied")

        # Get flashcard learning materials
        materials_result = await self.db.execute(
            select(LearningMaterial)
            .filter(
                LearningMaterial.book_id == book_id,
                LearningMaterial.user_id == user_id,
                LearningMaterial.material_type == "flashcard"
            )
        )
        materials = materials_result.scalars().all()

        # Convert SQLAlchemy models to Pydantic models
        pydantic_materials = []
        for material in materials:
            pydantic_material = PydanticLearningMaterial(
                id=str(material.id),
                user_id=str(material.user_id),
                book_id=str(material.book_id),
                material_type=material.material_type,
                title=material.title,
                content=material.content,
                additional_metadata=material.additional_metadata,
                created_at=material.created_at,
                updated_at=material.updated_at
            )
            pydantic_materials.append(pydantic_material)

        return pydantic_materials

    async def create_flashcard(
        self,
        user_id: str,
        book_id: str,
        question: str,
        answer: str,
        explanation: Optional[str] = None
    ) -> PydanticLearningMaterial:
        """
        Create a single flashcard directly.
        
        Args:
            user_id: ID of the user creating the flashcard
            book_id: ID of the related book
            question: The question for the flashcard
            answer: The answer for the flashcard
            explanation: Optional explanation for the answer
        
        Returns:
            Created flashcard learning material
        """
        # Verify user has access to the book
        book_result = await self.db.execute(
            select(Book).filter(Book.id == book_id, Book.user_id == user_id)
        )
        book = book_result.scalars().first()

        if not book:
            raise ValueError("Book not found or access denied")

        # Create learning material for the flashcard
        learning_material = LearningMaterial(
            user_id=user_id,
            book_id=book_id,
            material_type="flashcard",
            title=f"Flashcard: {question[:50]}...",
            content=f"Q: {question}\nA: {answer}\nExplanation: {explanation or ''}",
            additional_metadata={
                "question": question,
                "answer": answer,
                "explanation": explanation or "",
                "difficulty": "medium"  # Default difficulty
            }
        )
        self.db.add(learning_material)
        await self.db.commit()
        await self.db.refresh(learning_material)

        # Convert to Pydantic model
        pydantic_material = PydanticLearningMaterial(
            id=str(learning_material.id),
            user_id=str(learning_material.user_id),
            book_id=str(learning_material.book_id),
            material_type=learning_material.material_type,
            title=learning_material.title,
            content=learning_material.content,
            additional_metadata=learning_material.additional_metadata,
            created_at=learning_material.created_at,
            updated_at=learning_material.updated_at
        )

        return pydantic_material