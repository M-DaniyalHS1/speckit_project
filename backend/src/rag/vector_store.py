"""Vector store implementation using ChromaDB for the AI-Enhanced Interactive Book Agent.

This module provides a vector store interface for semantic search and retrieval
of book content using embeddings.
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from backend.src.config import settings


class VectorStore:
    """ChromaDB vector store for semantic search functionality."""
    
    def __init__(self):
        """Initialize the ChromaDB client and create/get the collection."""
        # Configure ChromaDB settings
        chroma_settings = Settings(
            anonymized_telemetry=False,
            persist_directory=settings.chromadb_path
        )

        # Initialize the ChromaDB client
        self.client = chromadb.Client(chroma_settings)

        # Get or create the collection for book content
        self.collection_name = "book_contents"
        try:
            # Try to get existing collection
            self.collection = self.client.get_collection(self.collection_name)
        except:
            # Create new collection if it doesn't exist
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
    
    async def add_document(
        self, 
        doc_id: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> bool:
        """Add a document to the vector store.
        
        Args:
            doc_id: Unique identifier for the document
            content: Text content of the document
            metadata: Optional metadata associated with the document
            embedding: Optional pre-computed embedding
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # If no embedding is provided, we'll let ChromaDB compute it
            if embedding is None:
                self.collection.add(
                    documents=[content],
                    metadatas=[metadata] if metadata else [{}],
                    ids=[doc_id]
                )
            else:
                # Use provided embedding
                self.collection.add(
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[metadata] if metadata else [{}],
                    ids=[doc_id]
                )
            return True
        except Exception as e:
            # Log the error in a real application
            print(f"Error adding document to vector store: {str(e)}")
            return False
    
    async def search(
        self, 
        query: str, 
        n_results: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents to the query.
        
        Args:
            query: Query text to find similar documents
            n_results: Number of results to return
            metadata_filter: Optional filter for metadata fields
            
        Returns:
            List of dictionaries containing documents, distances, and metadata
        """
        try:
            # Perform similarity search
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=metadata_filter
            )
            
            # Format the results
            formatted_results = []
            for i in range(len(results['documents'][0])):
                result = {
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'distance': results['distances'][0][i],
                    'metadata': results['metadatas'][0][i]
                }
                formatted_results.append(result)
                
            return formatted_results
        except Exception as e:
            # Log the error in a real application
            print(f"Error searching vector store: {str(e)}")
            return []
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the vector store.
        
        Args:
            doc_id: ID of the document to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            # Log the error in a real application
            print(f"Error deleting document from vector store: {str(e)}")
            return False
    
    async def update_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> bool:
        """Update an existing document in the vector store.
        
        Args:
            doc_id: ID of the document to update
            content: New content for the document
            metadata: New metadata for the document
            embedding: New embedding for the document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete the existing document
            await self.delete_document(doc_id)
            
            # Add the updated document
            return await self.add_document(doc_id, content, metadata, embedding)
        except Exception as e:
            # Log the error in a real application
            print(f"Error updating document in vector store: {str(e)}")
            return False
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific document by ID.
        
        Args:
            doc_id: ID of the document to retrieve
            
        Returns:
            Document data or None if not found
        """
        try:
            result = self.collection.get(ids=[doc_id])
            
            if result['documents']:
                return {
                    'id': result['ids'][0],
                    'content': result['documents'][0],
                    'metadata': result['metadatas'][0]
                }
            else:
                return None
        except Exception as e:
            # Log the error in a real application
            print(f"Error retrieving document from vector store: {str(e)}")
            return None
    
    async def get_all_document_ids(self) -> List[str]:
        """Get all document IDs in the collection.
        
        Returns:
            List of all document IDs
        """
        try:
            result = self.collection.get(include=['ids'])
            return result['ids']
        except Exception as e:
            # Log the error in a real application
            print(f"Error retrieving document IDs from vector store: {str(e)}")
            return []


# Global instance of the vector store
vector_store = None


async def init_vector_store():
    """Initialize the vector store."""
    global vector_store
    vector_store = VectorStore()