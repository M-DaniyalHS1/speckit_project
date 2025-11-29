"""Embedding generation service for the AI-Enhanced Interactive Book Agent."""
from typing import List, Dict, Any, Optional
import numpy as np
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from backend.src.config import settings


class EmbeddingGenerator:
    """Service for generating embeddings for text chunks using Google's Generative AI."""

    def __init__(self):
        """Initialize the embedding generator with the configured model."""
        self.embeddings_model = None
        if settings.google_api_key:
            self.embeddings_model = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=settings.google_api_key
            )
        else:
            print("Warning: Google API key is not configured. Embedding generation will not work until configured.")

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text chunk.

        Args:
            text: Input text to generate embedding for

        Returns:
            Embedding vector as a list of floats, or None if generation fails
        """
        try:
            if not text or not text.strip():
                return None

            if not self.embeddings_model:
                print("Embedding model not configured. Please set the Google API key.")
                return None

            # Generate embedding using the Google model
            embedding = self.embeddings_model.embed_query(text)
            return embedding
        except Exception as e:
            print(f"Error generating embedding for text: {str(e)}")
            return None

    async def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for a batch of text chunks.

        Args:
            texts: List of input texts to generate embeddings for

        Returns:
            List of embedding vectors (some may be None if generation failed)
        """
        if not texts:
            return []

        embeddings = []
        for text in texts:
            try:
                if text and text.strip():
                    embedding = await self.generate_embedding(text)
                    embeddings.append(embedding)
                else:
                    embeddings.append(None)
            except Exception as e:
                print(f"Error generating embedding for text in batch: {str(e)}")
                embeddings.append(None)

        return embeddings

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embedding vectors.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score between 0 and 1
        """
        if not embedding1 or not embedding2 or len(embedding1) != len(embedding2):
            return 0.0

        # Convert to numpy arrays for calculation
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        return float(similarity)

    def find_most_similar(self, query_embedding: List[float], 
                         embeddings: List[List[float]]) -> List[Dict[str, Any]]:
        """Find the most similar embeddings to the query embedding.

        Args:
            query_embedding: Embedding to compare against
            embeddings: List of embeddings to search through

        Returns:
            List of dictionaries containing similarity scores and indices,
            sorted by similarity in descending order
        """
        if not query_embedding or not embeddings:
            return []

        similarities = []
        for idx, embedding in enumerate(embeddings):
            if embedding:
                similarity = self.calculate_similarity(query_embedding, embedding)
                similarities.append({
                    "index": idx,
                    "similarity": similarity
                })

        # Sort by similarity in descending order
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities

    async def embed_chunks(self, chunks: List[str]) -> List[Dict[str, Any]]:
        """Generate embeddings for text chunks and return with metadata.

        Args:
            chunks: List of text chunks to embed

        Returns:
            List of dictionaries containing the chunk, its embedding, and metadata
        """
        if not chunks:
            return []

        # Generate embeddings for all chunks
        embeddings = await self.generate_embeddings_batch(chunks)

        # Create result list with chunk data and embeddings
        result = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            if embedding is not None:
                result.append({
                    "chunk_id": f"chunk_{i}",
                    "chunk_text": chunk,
                    "embedding": embedding,
                    "embedding_length": len(embedding),
                    "chunk_index": i
                })

        return result


# Global instance of the embedding generator
embedding_generator = EmbeddingGenerator()