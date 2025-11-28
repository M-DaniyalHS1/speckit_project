"""Service layer for search operations in AI-Enhanced Interactive Book Agent."""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from backend.src.models.sqlalchemy_models import BookContent, Query as SQLAlchemyQuery, Book
from backend.src.models.query import Query as PydanticQuery
from backend.src.rag.rag_engine import RAGEngine


class SearchService:
    """Service class for handling search operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the service with a database session."""
        self.db = db
        # Initialize the RAG engine for semantic search
        self.rag_engine = RAGEngine()

    async def search_content(self, book_id: str, query_text: str) -> List[dict]:
        """Perform semantic search within a specific book."""
        try:
            # Validate UUID format
            uuid.UUID(book_id)
        except ValueError:
            raise ValueError(f"Invalid book ID: {book_id}")
        
        # Perform the semantic search
        results = await self.rag_engine.search_similar_content(book_id, query_text)
        
        # Return the results (already formatted by the RAG engine)
        return results

    async def global_search(self, user_id: str, query_text: str) -> List[dict]:
        """Perform semantic search across all of a user's books."""
        # Get all books for the user
        books_result = await self.db.execute(
            select(Book).filter(Book.user_id == user_id)
        )
        books = books_result.scalars().all()
        
        all_results = []
        for book in books:
            # Perform search in each book
            book_results = await self.rag_engine.search_similar_content(str(book.id), query_text)
            all_results.extend(book_results)
        
        # Sort results by relevance (assuming they have a relevance score)
        all_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return all_results

    async def get_search_history(self, book_id: str) -> List[PydanticQuery]:
        """Get search history for a specific book."""
        try:
            # Validate UUID format
            uuid.UUID(book_id)
        except ValueError:
            raise ValueError(f"Invalid book ID: {book_id}")
            
        result = await self.db.execute(
            select(SQLAlchemyQuery)
            .filter(SQLAlchemyQuery.book_id == book_id)
            .order_by(SQLAlchemyQuery.created_at.desc())
        )
        queries = result.scalars().all()
        
        return [self._convert_sqlalchemy_to_pydantic(query) for query in queries]

    def _convert_sqlalchemy_to_pydantic(self, db_query: SQLAlchemyQuery) -> PydanticQuery:
        """
        Convert SQLAlchemy Query model to Pydantic Query model.
        """
        return PydanticQuery(
            id=str(db_query.id),
            user_id=str(db_query.user_id),
            book_id=str(db_query.book_id) if db_query.book_id else None,
            query_text=db_query.query_text,
            query_type=db_query.query_type,
            context=db_query.context,
            created_at=db_query.created_at
        )