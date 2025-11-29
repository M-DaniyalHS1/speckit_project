"""Document processing service for the AI-Enhanced Interactive Book Agent."""
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.src.rag.document_processor import document_processor
from backend.src.rag.vector_store import vector_store
from backend.src.rag.pipeline import rag_pipeline
from backend.src.models.sqlalchemy_models import Book, BookContent
from backend.src.models.book import Book as PydanticBook


class BookProcessor:
    """Service for processing books and preparing them for RAG functionality."""
    
    def __init__(self):
        """Initialize the book processor with required components."""
        if vector_store is None:
            raise ValueError("Vector store must be initialized before creating BookProcessor")
        
        if rag_pipeline is None:
            raise ValueError("RAG pipeline must be initialized before creating BookProcessor")
    
    async def process_book(self, db: AsyncSession, book_id: str) -> bool:
        """Process a book file to extract content and prepare it for search.
        
        Args:
            db: Database session
            book_id: ID of the book to process
            
        Returns:
            True if processing was successful, False otherwise
        """
        try:
            # Get the book from the database
            book_result = await db.execute(
                select(Book).filter(Book.id == book_id)
            )
            book = book_result.scalars().first()
            
            if not book:
                logging.error(f"Book with ID {book_id} not found in database")
                return False
            
            file_path = book.file_path
            if not Path(file_path).exists():
                logging.error(f"Book file does not exist: {file_path}")
                # Update book record to indicate processing error
                await self._update_processing_status(db, book_id, False, f"File does not exist: {file_path}")
                return False
            
            # Process the document using the document processor
            chunks_with_metadata = await document_processor.process_document(
                file_path=file_path,
                chunk_size=1000,
                overlap=100
            )
            
            # Store the chunks in the database
            chunk_count = 0
            for chunk_text, chunk_metadata in chunks_with_metadata:
                # Create BookContent record
                book_content = BookContent(
                    book_id=book.id,
                    chunk_id=chunk_metadata['chunk_id'],
                    content=chunk_text,
                    page_number=chunk_metadata.get('page_number'),
                    section_title=chunk_metadata.get('section_title', ''),
                    chapter=chunk_metadata.get('chapter', ''),
                    embedding_id=chunk_metadata.get('chunk_id')  # Using chunk_id as embedding reference
                )
                
                db.add(book_content)
                chunk_count += 1
            
            # Update the book's processing status
            await self._update_processing_status(db, book_id, True, None)
            
            # Commit changes to database
            await db.commit()
            
            # Add the document to the RAG system
            success = await rag_pipeline.add_document_to_rag(
                doc_id=book_id,
                file_path=file_path,
                metadata={
                    "book_id": book_id,
                    "title": book.title,
                    "author": book.author,
                    "user_id": str(book.user_id)
                }
            )
            
            if success:
                logging.info(f"Successfully processed book {book_id}, created {chunk_count} content chunks")
                return True
            else:
                logging.error(f"Failed to add book {book_id} to RAG system")
                return False
                
        except Exception as e:
            logging.error(f"Error processing book {book_id}: {str(e)}")
            await self._update_processing_status(db, book_id, False, str(e))
            return False
    
    async def _update_processing_status(
        self, 
        db: AsyncSession, 
        book_id: str, 
        is_processed: bool, 
        processing_error: Optional[str]
    ) -> None:
        """Update the processing status of a book.
        
        Args:
            db: Database session
            book_id: ID of the book to update
            is_processed: Whether processing was successful
            processing_error: Error message if processing failed
        """
        from sqlalchemy import update
        
        stmt = (
            update(Book)
            .where(Book.id == book_id)
            .values(
                is_processed=is_processed,
                processing_error=processing_error
            )
        )
        await db.execute(stmt)
        await db.commit()
    
    async def extract_metadata_from_book(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from a book file.
        
        Args:
            file_path: Path to the book file
            
        Returns:
            Dictionary containing extracted metadata
        """
        return await document_processor.get_document_metadata(file_path)
    
    async def validate_book_format(self, file_path: str) -> bool:
        """Validate if a file is in a supported format for processing.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if format is supported, False otherwise
        """
        supported_extensions = {'.pdf', '.docx', '.epub', '.txt'}
        file_ext = Path(file_path).suffix.lower()
        return file_ext in supported_extensions


# Global instance of the book processor
book_processor = BookProcessor()