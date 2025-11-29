"""Tutoring assistance service for the AI-Enhanced Interactive Book Agent."""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from datetime import datetime

from backend.src.models.sqlalchemy_models import (
    Book, BookContent, Query as SQLAlchemyQuery, Explanation as SQLAlchemyExplanation, 
    LearningMaterial, User
)
from backend.src.models.query import Query as PydanticQuery
from backend.src.models.explanation import Explanation as PydanticExplanation
from backend.src.ai.hint_generator import HintGenerator
from backend.src.ai.explanation_generator import ExplanationGenerator
from backend.src.rag.retriever import retrieval_service


class TutoringService:
    """Service for providing tutoring-style assistance with hints and guided learning."""

    def __init__(self, db: AsyncSession):
        """Initialize the tutoring service with a database session."""
        self.db = db
        self.hint_generator = HintGenerator()
        self.explanation_generator = ExplanationGenerator()
        self.retrieval_service = retrieval_service

    async def get_guidance_for_topic(
        self,
        user_id: str,
        book_id: str,
        topic: str,
        difficulty_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Provide guidance on a specific topic within a book.
        
        Args:
            user_id: ID of the user requesting guidance
            book_id: ID of the book containing the topic
            topic: The topic the user needs help with
            difficulty_level: Level of difficulty for the explanation (beginner, intermediate, advanced)
        
        Returns:
            Structured guidance with explanations and hints
        """
        # Verify user has access to the book
        book_result = await self.db.execute(
            select(Book).filter(Book.id == book_id, Book.user_id == user_id)
        )
        book = book_result.scalars().first()

        if not book:
            raise ValueError("Book not found or access denied")

        # Retrieve relevant content for the topic
        results = await self.retrieval_service.retrieve_by_semantic_similarity(
            query=topic,
            book_id=book_id,
            top_k=5
        )

        if not results:
            return {
                "topic": topic,
                "message": f"No content found for the topic '{topic}' in this book.",
                "suggestions": ["Try searching for related terms", "Check other sections of the book"],
                "timestamp": datetime.utcnow().isoformat()
            }

        # Get the most relevant content
        relevant_content = results[0]['content']

        # Generate guidance with increasing levels of help
        hint = await self.hint_generator.generate_hint(relevant_content, topic)
        explanation = await self.explanation_generator.generate_explanation(
            content=relevant_content,
            query=topic,
            complexity_level=difficulty_level
        )

        # Also provide related concepts
        related_concepts = await self._find_related_concepts(topic, book_id)

        return {
            "topic": topic,
            "difficulty_level": difficulty_level,
            "hint": hint,
            "explanation": explanation,
            "related_content": {
                "section": results[0].get('metadata', {}).get('section_title', 'Unknown'),
                "similarity_score": results[0].get('similarity_score', 0.0)
            },
            "related_concepts": related_concepts,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def provide_step_by_step_help(
        self,
        user_id: str,
        book_id: str,
        problem_description: str
    ) -> List[Dict[str, str]]:
        """
        Provide step-by-step guidance for solving problems or understanding concepts.
        
        Args:
            user_id: ID of the user requesting help
            book_id: ID of the book containing the relevant content
            problem_description: Description of the problem or concept the user is struggling with
        
        Returns:
            List of steps to guide the user toward understanding
        """
        # Verify user has access to the book
        book_result = await self.db.execute(
            select(Book).filter(Book.id == book_id, Book.user_id == user_id)
        )
        book = book_result.scalars().first()

        if not book:
            raise ValueError("Book not found or access denied")

        # Find relevant content for the problem
        results = await self.retrieval_service.retrieve_by_semantic_similarity(
            query=problem_description,
            book_id=book_id,
            top_k=3
        )

        if not results:
            return [{
                "step": 1,
                "title": "General Guidance",
                "description": f"We couldn't find specific content about '{problem_description}' in this book. Try rephrasing your question.",
                "hint": "Consider looking at the table of contents or index for related topics."
            }]

        # Generate a step-by-step breakdown
        all_content = " ".join([result['content'] for result in results])
        
        steps = await self.hint_generator.generate_step_by_step_solution(
            content=all_content,
            problem=problem_description
        )

        return steps

    async def generate_practice_questions(
        self,
        user_id: str,
        book_id: str,
        topic: str,
        num_questions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate practice questions for a specific topic to reinforce learning.
        
        Args:
            user_id: ID of the user requesting questions
            book_id: ID of the book containing the topic
            topic: Topic to generate questions about
            num_questions: Number of questions to generate
        
        Returns:
            List of practice questions with hints and answers
        """
        # Verify user has access to the book
        book_result = await self.db.execute(
            select(Book).filter(Book.id == book_id, Book.user_id == user_id)
        )
        book = book_result.scalars().first()

        if not book:
            raise ValueError("Book not found or access denied")

        # Find content related to the topic
        results = await self.retrieval_service.retrieve_by_semantic_similarity(
            query=topic,
            book_id=book_id,
            top_k=5
        )

        if not results:
            return []

        all_content = " ".join([result['content'] for result in results])

        # Generate questions
        from backend.src.ai.question_generator import QuestionGenerator
        question_generator = QuestionGenerator()
        questions = await question_generator.generate_questions(
            content=all_content,
            num_questions=num_questions,
            question_type="mixed",
            difficulty="medium"
        )

        # Enhance each question with hints
        enhanced_questions = []
        for question in questions:
            hint = await self.hint_generator.generate_hint(all_content, question.get("question", ""))
            question["hint"] = hint
            enhanced_questions.append(question)

        return enhanced_questions

    async def track_learning_progress(
        self,
        user_id: str,
        book_id: str,
        topic_interactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Track user's learning progress and identify areas needing more attention.
        
        Args:
            user_id: ID of the user
            book_id: ID of the book
            topic_interactions: List of interactions with different topics
        
        Returns:
            Assessment of learning progress and recommendations
        """
        # Verify user has access to the book
        book_result = await self.db.execute(
            select(Book).filter(Book.id == book_id, Book.user_id == user_id)
        )
        book = book_result.scalars().first()

        if not book:
            raise ValueError("Book not found or access denied")

        # Analyze interactions to identify patterns
        weak_areas = []
        strong_areas = []
        
        for interaction in topic_interactions:
            topic = interaction.get("topic", "")
            success_rate = interaction.get("success_rate", 0.0)
            
            if success_rate < 0.6:  # Less than 60% success
                weak_areas.append({"topic": topic, "success_rate": success_rate})
            elif success_rate > 0.8:  # Greater than 80% success
                strong_areas.append({"topic": topic, "success_rate": success_rate})

        # Provide recommendations based on analysis
        recommendations = []
        if weak_areas:
            recommendations.append({
                "type": "review",
                "message": f"You might benefit from reviewing these topics: {[w['topic'] for w in weak_areas]}",
                "suggested_activities": [
                    "Re-read relevant book sections",
                    "Practice more questions on these topics",
                    "Seek additional explanations"
                ]
            })
        
        if strong_areas:
            recommendations.append({
                "type": "advance",
                "message": f"You're doing well with {[s['topic'] for s in strong_areas]}. Consider advancing to more challenging material.",
                "suggested_activities": [
                    "Move on to next chapters",
                    "Try advanced problems",
                    "Teach these concepts to someone else"
                ]
            })

        return {
            "user_id": user_id,
            "book_id": book_id,
            "weak_areas": weak_areas,
            "strong_areas": strong_areas,
            "recommendations": recommendations,
            "assessment_date": datetime.utcnow().isoformat()
        }

    async def provide_contextual_help(
        self,
        user_id: str,
        book_id: str,
        current_location: str,
        user_question: str
    ) -> Dict[str, str]:
        """
        Provide contextual help based on where the user is in the book.
        
        Args:
            user_id: ID of the user requesting help
            book_id: ID of the book
            current_location: Current location in the book (chapter, page, etc.)
            user_question: Specific question from the user
        
        Returns:
            Contextual help and resources
        """
        # Verify user has access to the book
        book_result = await self.db.execute(
            select(Book).filter(Book.id == book_id, Book.user_id == user_id)
        )
        book = book_result.scalars().first()

        if not book:
            raise ValueError("Book not found or access denied")

        # Find content near the user's current location
        content_result = await self.db.execute(
            select(BookContent).filter(
                BookContent.book_id == book_id,
                BookContent.current_location.like(f"%{current_location}%")  # Simplified location matching
            ).limit(3)
        )
        nearby_content = content_result.scalars().all()

        if not nearby_content:
            # If no content matches the exact location, broaden the search
            nearby_content_result = await self.db.execute(
                select(BookContent)
                .filter(BookContent.book_id == book_id)
                .order_by(BookContent.created_at.desc())
                .limit(3)
            )
            nearby_content = nearby_content_result.scalars().all()

        if not nearby_content:
            return {
                "message": "Could not find content near your current location",
                "general_hint": await self.hint_generator.generate_general_hint(user_question)
            }

        # Combine nearby content for context
        context_content = " ".join([content.content for content in nearby_content])
        
        # Generate contextual help
        explanation = await self.explanation_generator.generate_explanation(
            content=context_content,
            query=user_question,
            complexity_level="intermediate"
        )

        hint = await self.hint_generator.generate_hint(context_content, user_question)

        return {
            "location": current_location,
            "explanation": explanation,
            "hint": hint,
            "context_snippet": context_content[:200] + "..." if len(context_content) > 200 else context_content
        }

    async def _find_related_concepts(self, topic: str, book_id: str) -> List[str]:
        """Helper method to find related concepts for a given topic."""
        # This would typically involve more sophisticated semantic analysis
        # For now, we'll return a placeholder implementation
        # In a real implementation, this would search for semantically related terms
        return [topic]  # Placeholder