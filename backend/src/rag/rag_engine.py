"""RAG (Retrieval-Augmented Generation) engine for the AI-Enhanced Interactive Book Agent."""
from typing import List, Dict, Any
import asyncio
import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from backend.src.models.sqlalchemy_models import BookContent
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.src.config import settings


class RAGEngine:
    """RAG engine for semantic search and content retrieval."""

    def __init__(self):
        """Initialize the RAG engine with ChromaDB and embedding model."""
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(path=settings.chromadb_path)

        # Initialize the embedding model using Google's Generative AI
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=settings.google_api_key
        )

        # Text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    async def search_similar_content(self, book_id: str, query: str) -> List[Dict[str, Any]]:
        """
        Search for content similar to the query within a specific book.

        Args:
            book_id: ID of the book to search in
            query: Query text to search for

        Returns:
            List of similar content chunks with metadata
        """
        # Get the ChromaDB collection for this book
        collection_name = f"book_{book_id}"

        try:
            collection = self.chroma_client.get_collection(name=collection_name)
        except:
            # If the collection doesn't exist, return empty results
            return []

        # Generate embedding for the query
        query_embedding = self.embeddings.embed_query(query)

        # Perform similarity search in the collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5  # Return top 5 most similar results
        )

        # Format the results to match the expected structure
        formatted_results = []
        if results and 'ids' in results and results['ids']:
            ids = results['ids'][0]
            documents = results['documents'][0] if results['documents'] else []
            metadatas = results['metadatas'][0] if results['metadatas'] else []
            distances = results['distances'][0] if results['distances'] else []

            for i in range(len(ids)):
                formatted_results.append({
                    "id": ids[i],
                    "content": documents[i] if i < len(documents) else "",
                    "page_number": metadatas[i].get('page_number', None) if i < len(metadatas) and metadatas[i] else None,
                    "section_title": metadatas[i].get('section_title', None) if i < len(metadatas) and metadatas[i] else None,
                    "relevance_score": 1 - distances[i] if i < len(distances) else 0,  # Convert distance to similarity score
                    "source": f"Book {book_id}"
                })

        return formatted_results

    async def add_book_content_to_index(self, db: AsyncSession, book_id: str):
        """
        Add book content to the search index.

        Args:
            db: Database session
            book_id: ID of the book to index

        Returns:
            Dictionary with indexing results
        """
        # Get all content chunks for the book
        result = await db.execute(
            select(BookContent)
            .filter(BookContent.book_id == book_id)
        )
        content_chunks = result.scalars().all()

        if not content_chunks:
            return {"book_id": book_id, "indexed_chunks": 0, "message": "No content found to index"}

        # Prepare documents, metadata, and IDs for ChromaDB
        documents = []
        metadatas = []
        ids = []

        for chunk in content_chunks:
            documents.append(chunk.content)
            metadatas.append({
                "page_number": chunk.page_number,
                "section_title": chunk.section_title,
                "chunk_id": chunk.chunk_id,
                "book_id": book_id
            })
            ids.append(chunk.id)  # Using the SQLAlchemy BookContent ID as the ChromaDB ID

        # Get or create the collection for this book
        collection_name = f"book_{book_id}"
        collection = self.chroma_client.get_or_create_collection(
            name=collection_name
        )

        # Generate embeddings for the documents
        embeddings = [self.embeddings.embed_query(doc) for doc in documents]

        # Add the documents to the collection
        collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        return {"book_id": book_id, "indexed_chunks": len(content_chunks), "message": "Successfully indexed content"}