"""Citation service for the AI-Enhanced Interactive Book Agent."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.src.models.sqlalchemy_models import Book, BookContent
from backend.src.config import settings


class CitationService:
    """Service for generating proper citations for search results and AI responses."""

    def __init__(self):
        """Initialize the citation service."""
        pass

    def generate_citation(self, 
                         content_chunk: Dict[str, Any], 
                         book_info: Dict[str, Any],
                         context: str = "search_result") -> str:
        """Generate a proper citation for a content chunk.

        Args:
            content_chunk: Dictionary containing chunk information
            book_info: Dictionary containing book metadata
            context: Context for the citation ('search_result', 'explanation', 'summary')

        Returns:
            Formatted citation string
        """
        # Extract necessary information from the content chunk
        page_number = content_chunk.get('page_number', content_chunk.get('page_num'))
        section_title = content_chunk.get('section_title', content_chunk.get('section', ''))
        chapter = content_chunk.get('chapter', '')
        source = content_chunk.get('source', book_info.get('title', 'Unknown Book'))
        
        # Determine the citation format based on context
        if context == "search_result":
            return self._format_search_citation(book_info, page_number, section_title, chapter)
        elif context == "explanation":
            return self._format_explanation_citation(book_info, page_number, section_title)
        elif context == "summary":
            return self._format_summary_citation(book_info, page_number, section_title)
        else:
            return self._format_general_citation(book_info, page_number, section_title)

    def _format_search_citation(self, book_info: Dict[str, Any], 
                               page_number: Optional[int], 
                               section_title: str,
                               chapter: str) -> str:
        """Format a citation for search results."""
        title = book_info.get('title', 'Unknown Title')
        author = book_info.get('author', 'Unknown Author')
        year = book_info.get('year', 'n.d.')
        
        citation_parts = [f"{author} ({year})"]
        
        if chapter:
            citation_parts.append(f"Chapter {chapter}")
        
        if section_title:
            citation_parts.append(f'"{section_title}"')
        
        if page_number:
            citation_parts.append(f"p. {page_number}")
        
        citation_parts.append(f"Book: {title}")
        
        return ". ".join(citation_parts) + "."

    def _format_explanation_citation(self, book_info: Dict[str, Any], 
                                    page_number: Optional[int], 
                                    section_title: str) -> str:
        """Format a citation for explanations."""
        title = book_info.get('title', 'Unknown Title')
        author = book_info.get('author', 'Unknown Author')
        
        citation_parts = [f"From: {title} by {author}"]
        
        if section_title:
            citation_parts.append(f'Section: "{section_title}"')
        
        if page_number:
            citation_parts.append(f"Page: {page_number}")
        
        return ". ".join(citation_parts) + "."

    def _format_summary_citation(self, book_info: Dict[str, Any], 
                                page_number: Optional[int], 
                                section_title: str) -> str:
        """Format a citation for summaries."""
        title = book_info.get('title', 'Unknown Title')
        
        citation_parts = [f"Source: {title}"]
        
        if section_title:
            citation_parts.append(f'Topic: "{section_title}"')
        
        if page_number:
            citation_parts.append(f"Located at page {page_number}")
        
        return ". ".join(citation_parts) + "."

    def _format_general_citation(self, book_info: Dict[str, Any], 
                                page_number: Optional[int], 
                                section_title: str) -> str:
        """Format a general citation."""
        title = book_info.get('title', 'Unknown Title')
        author = book_info.get('author', 'Unknown Author')
        
        citation_parts = [f"{author}. {title}"]
        
        if section_title:
            citation_parts.append(f'Section: "{section_title}"')
        
        if page_number:
            citation_parts.append(f"Page {page_number}")
        
        return ". ".join(citation_parts) + "."

    async def get_citation_info(self, db: AsyncSession, book_id: str, content_id: Optional[str] = None) -> Dict[str, Any]:
        """Get citation information for a specific book or content chunk.

        Args:
            db: Database session
            book_id: ID of the book
            content_id: Optional ID of specific content chunk

        Returns:
            Dictionary containing citation information
        """
        # Get book information
        book_result = await db.execute(
            select(Book).filter(Book.id == book_id)
        )
        book = book_result.scalars().first()
        
        if not book:
            return {}

        book_info = {
            "id": str(book.id),
            "title": book.title,
            "author": book.author,
            "year": book.created_at.year if book.created_at else None,
            "publisher": getattr(book, 'publisher', 'Unknown Publisher'),
            "isbn": getattr(book, 'isbn', 'Unknown ISBN')
        }

        # If a specific content ID is provided, get additional chunk information
        if content_id:
            content_result = await db.execute(
                select(BookContent).filter(BookContent.id == content_id)
            )
            content = content_result.scalars().first()

            if content:
                book_info.update({
                    "page_number": content.page_number,
                    "section_title": content.section_title,
                    "chapter": content.chapter
                })

        return book_info

    def format_multiple_citations(self, 
                                 results: List[Dict[str, Any]], 
                                 book_info: Dict[str, Any],
                                 context: str = "search_result") -> List[Dict[str, Any]]:
        """Format citations for multiple search results.

        Args:
            results: List of search results
            book_info: Dictionary containing book metadata
            context: Context for the citations

        Returns:
            List of search results with formatted citations
        """
        formatted_results = []

        for i, result in enumerate(results):
            # Create a copy of the result
            formatted_result = result.copy()
            
            # Generate citation for this specific result
            citation = self.generate_citation(result, book_info, context)
            
            # Add citation to the result
            formatted_result['citation'] = citation
            formatted_result['citation_order'] = i + 1
            
            formatted_results.append(formatted_result)

        return formatted_results

    def validate_citation_format(self, citation: str) -> bool:
        """Validate that a citation follows proper format.

        Args:
            citation: Citation string to validate

        Returns:
            True if citation format is valid, False otherwise
        """
        # Basic validation - checks if citation contains essential elements
        required_elements = ['.', 'From:', 'Page:', 'Book:']  # Basic required elements
        return any(element in citation for element in required_elements) or len(citation) > 10


# Global instance of the citation service
citation_service = CitationService()