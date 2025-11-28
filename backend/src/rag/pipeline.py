"""Langchain integration for the RAG pipeline in the AI-Enhanced Interactive Book Agent.

This module sets up the Retrieval-Augmented Generation pipeline using Langchain
components to connect document processing, vector storage, and AI generation.
"""
from typing import List, Dict, Any, Optional
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from backend.src.rag.vector_store import vector_store
from backend.src.ai.gemini_client import gemini_client
from backend.src.rag.document_processor import document_processor
from backend.src.config import settings


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline using Langchain."""
    
    def __init__(self):
        """Initialize the RAG pipeline components."""
        if vector_store is None:
            raise ValueError("Vector store must be initialized before creating RAG pipeline")
        
        if gemini_client is None:
            raise ValueError("Gemini client must be initialized before creating RAG pipeline")
    
    async def add_document_to_rag(
        self, 
        doc_id: str, 
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Process a document and add it to the vector store for RAG.
        
        Args:
            doc_id: Unique identifier for the document
            file_path: Path to the document file
            metadata: Optional additional metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Process the document into chunks
            chunks_with_metadata = await document_processor.process_document(file_path)
            
            # Add each chunk to the vector store
            for i, (chunk_text, chunk_meta) in enumerate(chunks_with_metadata):
                # Merge provided metadata with chunk-specific metadata
                final_metadata = chunk_meta.copy()
                if metadata:
                    final_metadata.update(metadata)
                
                # Create a unique ID for this chunk
                chunk_doc_id = f"{doc_id}_chunk_{i}"
                
                # Add to vector store
                success = await vector_store.add_document(
                    doc_id=chunk_doc_id,
                    content=chunk_text,
                    metadata=final_metadata
                )
                
                if not success:
                    print(f"Failed to add chunk {chunk_doc_id} to vector store")
                    return False
            
            return True
        except Exception as e:
            print(f"Error adding document to RAG: {str(e)}")
            return False
    
    async def query_rag(self, query: str, n_results: int = 5) -> str:
        """Query the RAG system to get an AI-generated response based on document content.
        
        Args:
            query: The user's query
            n_results: Number of relevant documents to retrieve
            
        Returns:
            AI-generated response based on retrieved documents
        """
        try:
            # Retrieve relevant documents from vector store
            search_results = await vector_store.search(query=query, n_results=n_results)
            
            if not search_results:
                return "I couldn't find any relevant information in the documents to answer your query."
            
            # Format retrieved documents for the prompt
            context_parts = []
            for result in search_results:
                content = result['content']
                # Add citation info if available
                metadata = result.get('metadata', {})
                source_info = f" (Source: {metadata.get('file_name', 'Unknown')})" if metadata else ""
                context_parts.append(f"{content}{source_info}")
            
            context = "\n\n".join(context_parts)
            
            # Generate response using the AI model with context
            response = await gemini_client.generate_content(
                prompt=query,
                context=context,
                temperature=0.7,
                max_output_tokens=1024
            )
            
            return response
        except Exception as e:
            print(f"Error querying RAG: {str(e)}")
            # Fallback response
            return "I encountered an error while processing your query. Please try again."
    
    async def query_rag_with_sources(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """Query the RAG system and return both response and source information.
        
        Args:
            query: The user's query
            n_results: Number of relevant documents to retrieve
            
        Returns:
            Dictionary containing response and source information
        """
        try:
            # Retrieve relevant documents from vector store
            search_results = await vector_store.search(query=query, n_results=n_results)
            
            if not search_results:
                return {
                    "response": "I couldn't find any relevant information in the documents to answer your query.",
                    "sources": []
                }
            
            # Format retrieved documents for the prompt
            context_parts = []
            sources = []
            for result in search_results:
                content = result['content']
                doc_id = result['id']
                distance = result['distance']
                
                # Add citation info if available
                metadata = result.get('metadata', {})
                source_info = {
                    'id': doc_id,
                    'distance': distance,
                    'file_name': metadata.get('file_name', 'Unknown'),
                    'chunk_index': metadata.get('chunk_index', -1),
                    'page_number': metadata.get('page_number', None),
                    'section_title': metadata.get('section_title', ''),
                    'content_preview': content[:200] + "..." if len(content) > 200 else content
                }
                sources.append(source_info)
                
                context_parts.append(f"{content}")
            
            context = "\n\n".join(context_parts)
            
            # Generate response using the AI model with context
            response = await gemini_client.generate_content(
                prompt=query,
                context=context,
                temperature=0.7,
                max_output_tokens=1024
            )
            
            return {
                "response": response,
                "sources": sources
            }
        except Exception as e:
            print(f"Error querying RAG with sources: {str(e)}")
            return {
                "response": "I encountered an error while processing your query. Please try again.",
                "sources": []
            }
    
    async def delete_document_from_rag(self, doc_id: str) -> bool:
        """Remove a document and all its chunks from the RAG system.
        
        Args:
            doc_id: ID of the document to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all document IDs to identify chunks belonging to this document
            all_ids = await vector_store.get_all_document_ids()
            
            # Filter for chunks belonging to this document
            chunk_ids_to_delete = [id for id in all_ids if id.startswith(f"{doc_id}_chunk_")]
            
            # Delete each chunk
            for chunk_id in chunk_ids_to_delete:
                success = await vector_store.delete_document(chunk_id)
                if not success:
                    print(f"Failed to delete chunk {chunk_id}")
                    return False
            
            return True
        except Exception as e:
            print(f"Error deleting document from RAG: {str(e)}")
            return False


# Global instance of the RAG pipeline
rag_pipeline = None


async def init_rag_pipeline():
    """Initialize the RAG pipeline."""
    global rag_pipeline
    rag_pipeline = RAGPipeline()