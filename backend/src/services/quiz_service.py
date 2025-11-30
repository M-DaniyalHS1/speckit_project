"""Quiz generation service for the AI-Enhanced Interactive Book Agent.

This service handles the generation of quizzes from book content using AI,
including various question types and difficulty levels.
"""
import asyncio
import random
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.src.models.sqlalchemy_models import Book, BookContent, User
from backend.src.models.learning_material import LearningMaterial
from backend.src.ai.question_generator import QuestionGenerator
from backend.src.rag.retriever import retrieval_service
from backend.src.config import settings


class QuizService:
    """Service for generating quizzes from book content using AI."""

    def __init__(self, db: AsyncSession):
        """Initialize the quiz service with a database session."""
        self.db = db
        self.question_generator = QuestionGenerator()
        self.retrieval_service = retrieval_service

    async def generate_quiz(
        self,
        user_id: str,
        book_id: str,
        content_id: Optional[str] = None,
        num_questions: int = 10,
        difficulty: str = "medium",
        question_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a quiz based on book content.

        Args:
            user_id: ID of the user requesting the quiz
            book_id: ID of the book to generate quiz from
            content_id: Optional specific content ID to focus on (if None, uses whole book)
            num_questions: Number of questions to generate
            difficulty: Difficulty level ("easy", "medium", "hard")
            question_types: List of question types to include (e.g., ["multiple_choice", "short_answer"])

        Returns:
            Dictionary containing the quiz with questions and metadata
        """
        if not question_types:
            question_types = ["multiple_choice"]

        # Verify user has access to the book
        book_result = await self.db.execute(
            select(Book).filter(Book.id == book_id, Book.user_id == user_id)
        )
        book = book_result.scalars().first()

        if not book:
            raise ValueError("Book not found or access denied")

        # Get content to generate quiz from
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
            raise ValueError("No content available for quiz generation")

        # Combine content for context
        all_content_text = " ".join([c.content for c in content])
        
        # Limit content length to avoid exceeding AI token limits
        max_content_length = 15000  # Adjust based on model's token limit
        if len(all_content_text) > max_content_length:
            all_content_text = all_content_text[:max_content_length]

        # Generate questions using AI
        quiz_questions = []
        
        # If multiple question types are requested, distribute questions among them
        questions_per_type = max(1, num_questions // len(question_types))
        remaining_questions = num_questions % len(question_types)
        
        for i, q_type in enumerate(question_types):
            num_for_this_type = questions_per_type
            if i < remaining_questions:
                num_for_this_type += 1  # Distribute remaining questions
            
            # Generate questions of this type
            questions = await self.question_generator.generate_questions(
                content=all_content_text,
                num_questions=num_for_this_type,
                question_type=q_type,
                difficulty=difficulty
            )
            
            # Add these questions to the quiz
            for q in questions:
                quiz_questions.append(q)
        
        # Shuffle the questions to mix different types
        random.shuffle(quiz_questions)
        
        # Limit to the exact number requested
        final_questions = quiz_questions[:num_questions]
        
        # Create learning material entry for the quiz
        quiz_material = LearningMaterial(
            user_id=user_id,
            book_id=book_id,
            material_type="quiz",
            title=f"Quiz on {book.title}",
            content=f"Quiz with {len(final_questions)} questions on {book.title}",
            additional_metadata={
                "num_questions": len(final_questions),
                "difficulty": difficulty,
                "question_types": question_types,
                "content_id": content_id,
            }
        )
        self.db.add(quiz_material)
        await self.db.commit()
        await self.db.refresh(quiz_material)

        # Create the quiz structure
        quiz = {
            "id": str(quiz_material.id),
            "title": f"Quiz on {book.title}",
            "book_id": book_id,
            "content_id": content_id,
            "num_questions": len(final_questions),
            "difficulty": difficulty,
            "question_types": question_types,
            "questions": final_questions,
            "metadata": {
                "generated_at": __import__('datetime').datetime.utcnow().isoformat(),
                "generator": "ai_quiz_generator",
                "source_content_length": len(all_content_text)
            }
        }

        return quiz

    async def generate_chapter_quiz(
        self,
        user_id: str,
        book_id: str,
        chapter_title: str,
        num_questions: int = 10,
        difficulty: str = "medium"
    ) -> Dict[str, Any]:
        """
        Generate a quiz focused on a specific chapter.

        Args:
            user_id: ID of the user requesting the quiz
            book_id: ID of the book to generate quiz from
            chapter_title: Title of the chapter to focus on
            num_questions: Number of questions to generate
            difficulty: Difficulty level ("easy", "medium", "hard")

        Returns:
            Dictionary containing the chapter quiz with questions and metadata
        """
        # Verify user has access to the book
        book_result = await self.db.execute(
            select(Book).filter(Book.id == book_id, Book.user_id == user_id)
        )
        book = book_result.scalars().first()

        if not book:
            raise ValueError("Book not found or access denied")

        # Search for content related to the chapter
        search_results = await self.retrieval_service.search_content(
            query=chapter_title,
            book_id=book_id,
            top_k=5  # Get top 5 most relevant chunks
        )

        if not search_results:
            raise ValueError(f"No content found for chapter: {chapter_title}")

        # Combine the most relevant content
        chapter_content = " ".join([result['content'] for result in search_results])
        
        # Limit content length to avoid exceeding AI token limits
        max_content_length = 15000
        if len(chapter_content) > max_content_length:
            chapter_content = chapter_content[:max_content_length]

        # Generate questions specifically for this chapter content
        questions = await self.question_generator.generate_questions(
            content=chapter_content,
            num_questions=num_questions,
            question_type="mixed",  # Mix of different question types
            difficulty=difficulty
        )

        # Create learning material entry for the chapter quiz
        quiz_material = LearningMaterial(
            user_id=user_id,
            book_id=book_id,
            material_type="chapter_quiz",
            title=f"Quiz on Chapter: {chapter_title}",
            content=f"Chapter quiz with {len(questions)} questions on '{chapter_title}'",
            additional_metadata={
                "num_questions": len(questions),
                "difficulty": difficulty,
                "chapter_title": chapter_title,
                "source_content_ids": [result['id'] for result in search_results]
            }
        )
        self.db.add(quiz_material)
        await self.db.commit()
        await self.db.refresh(quiz_material)

        # Create the chapter quiz structure
        quiz = {
            "id": str(quiz_material.id),
            "title": f"Quiz on Chapter: {chapter_title}",
            "book_id": book_id,
            "chapter_title": chapter_title,
            "num_questions": len(questions),
            "difficulty": difficulty,
            "questions": questions,
            "metadata": {
                "generated_at": __import__('datetime').datetime.utcnow().isoformat(),
                "generator": "ai_chapter_quiz_generator",
                "source_content_count": len(search_results),
                "chapter_content_length": len(chapter_content)
            }
        }

        return quiz

    async def generate_practice_quiz(
        self,
        user_id: str,
        book_id: str,
        focus_areas: Optional[List[str]] = None,
        num_questions: int = 10
    ) -> Dict[str, Any]:
        """
        Generate a practice quiz focusing on specific areas or concepts.

        Args:
            user_id: ID of the user requesting the quiz
            book_id: ID of the book to generate quiz from
            focus_areas: List of specific topics/concepts to focus on
            num_questions: Number of questions to generate

        Returns:
            Dictionary containing the practice quiz with questions and metadata
        """
        # Verify user has access to the book
        book_result = await self.db.execute(
            select(Book).filter(Book.id == book_id, Book.user_id == user_id)
        )
        book = book_result.scalars().first()

        if not book:
            raise ValueError("Book not found or access denied")

        # If focus areas are specified, get content related to those topics
        all_content = ""
        if focus_areas:
            for focus_area in focus_areas:
                search_results = await self.retrieval_service.search_content(
                    query=focus_area,
                    book_id=book_id,
                    top_k=3
                )
                area_content = " ".join([result['content'] for result in search_results])
                all_content += area_content + "\n\n"
        else:
            # If no focus areas, get all content for the book
            content_result = await self.db.execute(
                select(BookContent).filter(BookContent.book_id == book_id)
            )
            content = content_result.scalars().all()
            all_content = " ".join([c.content for c in content])

        if not all_content.strip():
            raise ValueError("No content available for quiz generation")

        # Limit content length
        max_content_length = 15000
        if len(all_content) > max_content_length:
            all_content = all_content[:max_content_length]

        # Generate questions focusing on the specified topics
        questions = await self.question_generator.generate_questions(
            content=all_content,
            num_questions=num_questions,
            question_type="practice",
            difficulty="medium",  # Medium difficulty for practice
            focus_areas=focus_areas
        )

        # Create learning material entry for the practice quiz
        quiz_material = LearningMaterial(
            user_id=user_id,
            book_id=book_id,
            material_type="practice_quiz",
            title=f"Practice Quiz on {', '.join(focus_areas) if focus_areas else 'Book Topics'}",
            content=f"Practice quiz with {len(questions)} questions on specified topics",
            additional_metadata={
                "num_questions": len(questions),
                "difficulty": "medium",
                "focus_areas": focus_areas,
            }
        )
        self.db.add(quiz_material)
        await self.db.commit()
        await self.db.refresh(quiz_material)

        # Create the practice quiz structure
        quiz = {
            "id": str(quiz_material.id),
            "title": f"Practice Quiz on {', '.join(focus_areas) if focus_areas else 'Book Topics'}",
            "book_id": book_id,
            "focus_areas": focus_areas,
            "num_questions": len(questions),
            "questions": questions,
            "metadata": {
                "generated_at": __import__('datetime').datetime.utcnow().isoformat(),
                "generator": "ai_practice_quiz_generator",
                "content_length": len(all_content)
            }
        }

        return quiz

    async def generate_vocabulary_quiz(
        self,
        user_id: str,
        book_id: str,
        num_questions: int = 10
    ) -> Dict[str, Any]:
        """
        Generate a vocabulary quiz from book content.

        Args:
            user_id: ID of the user requesting the quiz
            book_id: ID of the book to generate quiz from
            num_questions: Number of vocabulary questions to generate

        Returns:
            Dictionary containing the vocabulary quiz with questions and metadata
        """
        # Verify user has access to the book
        book_result = await self.db.execute(
            select(Book).filter(Book.id == book_id, Book.user_id == user_id)
        )
        book = book_result.scalars().first()

        if not book:
            raise ValueError("Book not found or access denied")

        # Get all content for the book
        content_result = await self.db.execute(
            select(BookContent).filter(BookContent.book_id == book_id)
        )
        content = content_result.scalars().all()

        if not content:
            raise ValueError("No content available for quiz generation")

        # Combine content for context
        all_content_text = " ".join([c.content for c in content])

        # Generate vocabulary questions
        questions = await self.question_generator.generate_vocabulary_questions(
            content=all_content_text,
            num_questions=num_questions
        )

        # Create learning material entry for the vocabulary quiz
        quiz_material = LearningMaterial(
            user_id=user_id,
            book_id=book_id,
            material_type="vocabulary_quiz",
            title=f"Vocabulary Quiz on {book.title}",
            content=f"Vocabulary quiz with {len(questions)} questions on {book.title}",
            additional_metadata={
                "num_questions": len(questions),
                "question_type": "vocabulary",
            }
        )
        self.db.add(quiz_material)
        await self.db.commit()
        await self.db.refresh(quiz_material)

        # Create the vocabulary quiz structure
        quiz = {
            "id": str(quiz_material.id),
            "title": f"Vocabulary Quiz on {book.title}",
            "book_id": book_id,
            "num_questions": len(questions),
            "questions": questions,
            "metadata": {
                "generated_at": __import__('datetime').datetime.utcnow().isoformat(),
                "generator": "ai_vocabulary_quiz_generator",
                "content_length": len(all_content_text)
            }
        }

        return quiz

    async def save_quiz_results(
        self,
        user_id: str,
        quiz_id: str,
        answers: List[Dict[str, Any]],
        score: float
    ) -> bool:
        """
        Save quiz results for a user.

        Args:
            user_id: ID of the user taking the quiz
            quiz_id: ID of the quiz being taken
            answers: List of answers provided by the user
            score: Score achieved on the quiz (as a percentage)

        Returns:
            True if successful, False otherwise
        """
        try:
            # In a real implementation, we would store quiz results in a database
            # For now, we'll just verify the inputs are valid
            if not all(key in answer for answer in answers for key in ['question_id', 'selected_option', 'is_correct']):
                raise ValueError("Missing required fields in answers")

            # Find the learning material for this quiz
            material_result = await self.db.execute(
                select(LearningMaterial)
                .filter(LearningMaterial.id == quiz_id, LearningMaterial.user_id == user_id)
            )
            quiz_material = material_result.scalars().first()

            if not quiz_material:
                raise ValueError("Quiz not found or access denied")

            # Update the quiz material with result information
            if not quiz_material.additional_metadata:
                quiz_material.additional_metadata = {}
            quiz_material.additional_metadata['score'] = score
            quiz_material.additional_metadata['completed_at'] = __import__('datetime').datetime.utcnow().isoformat()
            quiz_material.additional_metadata['answers'] = answers

            await self.db.commit()
            await self.db.refresh(quiz_material)

            return True

        except Exception as e:
            print(f"Error saving quiz results: {str(e)}")
            await self.db.rollback()
            return False

    async def get_quiz_history(
        self,
        user_id: str,
        book_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get quiz history for a user.

        Args:
            user_id: ID of the user
            book_id: Optional book ID to filter quizzes for a specific book

        Returns:
            List of quiz histories
        """
        try:
            query = select(LearningMaterial).filter(
                LearningMaterial.user_id == user_id,
                LearningMaterial.material_type.like('%quiz%')
            )

            if book_id:
                query = query.filter(LearningMaterial.book_id == book_id)

            result = await self.db.execute(query)
            materials = result.scalars().all()

            quiz_histories = []
            for material in materials:
                quiz_history = {
                    "id": str(material.id),
                    "title": material.title,
                    "book_id": str(material.book_id),
                    "created_at": material.created_at.isoformat() if material.created_at else None,
                    "updated_at": material.updated_at.isoformat() if material.updated_at else None,
                    "metadata": material.additional_metadata or {}
                }

                quiz_histories.append(quiz_history)

            return quiz_histories

        except Exception as e:
            print(f"Error retrieving quiz history: {str(e)}")
            return []