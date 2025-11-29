"""Google Gemini API client for the AI-Enhanced Interactive Book Agent.

This module provides a client interface to interact with Google's Gemini API
for AI-powered features like content explanation, summarization, and learning tools.
"""
import asyncio
import google.generativeai as genai
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from backend.src.config import settings


class GeminiClient:
    """Client for interacting with Google Gemini API."""
    
    def __init__(self):
        """Initialize the Gemini client with API key from settings."""
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")

        genai.configure(api_key=settings.google_api_key)

        # Set up the default model
        self.default_model = genai.GenerativeModel(settings.gemini_model_name)
    
    async def generate_content(
        self, 
        prompt: str, 
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1024
    ) -> str:
        """Generate content using the Gemini model.
        
        Args:
            prompt: The main prompt to send to the model
            context: Additional context to provide to the model
            temperature: Controls randomness in output (0.0-1.0)
            max_output_tokens: Maximum number of tokens in the response
            
        Returns:
            Generated content as a string
        """
        try:
            # Combine context and prompt if context is provided
            full_prompt = prompt
            if context:
                full_prompt = f"Context: {context}\n\nQuestion: {prompt}"
            
            # Generate content
            response = self.default_model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens
                )
            )
            
            return response.text if response.text else ""
        except Exception as e:
            # Log the error in a real application
            raise Exception(f"Error generating content with Gemini: {str(e)}")
    
    async def embed_content(self, text: str) -> List[float]:
        """Generate embeddings for the given text.
        
        Args:
            text: Text to generate embeddings for
            
        Returns:
            List of embedding values
        """
        try:
            result = genai.embed_content(
                model="models/embedding-001",  # Default embedding model
                content=text,
                task_type="RETRIEVAL_DOCUMENT"
            )
            return result['embedding']
        except Exception as e:
            # Log the error in a real application
            raise Exception(f"Error generating embeddings with Gemini: {str(e)}")
    
    async def generate_explanation(
        self, 
        content: str, 
        explanation_type: str = "simple",
        user_level: str = "intermediate"
    ) -> str:
        """Generate an explanation for the given content.
        
        Args:
            content: The content to explain
            explanation_type: "simple" for basic explanation, "detailed" for in-depth
            user_level: User's knowledge level ("beginner", "intermediate", "advanced")
            
        Returns:
            Explanation as a string
        """
        prompt_type = {
            "simple": f"Explain the following content in simple terms for a {user_level} level reader:",
            "detailed": f"Provide a detailed explanation of the following content for a {user_level} level reader:"
        }.get(explanation_type, "simple")
        
        prompt = f"{prompt_type}\n\n{content}"
        return await self.generate_content(prompt)
    
    async def generate_summary(
        self,
        content: str,
        summary_type: str = "concise"
    ) -> str:
        """Generate a summary of the given content.
        
        Args:
            content: The content to summarize
            summary_type: "concise" for brief summary, "comprehensive" for detailed
            
        Returns:
            Summary as a string
        """
        prompt_type = {
            "concise": "Provide a concise summary of the following content:",
            "comprehensive": "Provide a comprehensive summary of the following content that covers all main points:"
        }.get(summary_type, "concise")
        
        prompt = f"{prompt_type}\n\n{content}"
        return await self.generate_content(prompt)
    
    async def generate_questions(
        self,
        content: str,
        num_questions: int = 5,
        question_type: str = "multiple-choice"
    ) -> List[str]:
        """Generate questions based on the given content.
        
        Args:
            content: Content to generate questions from
            num_questions: Number of questions to generate
            question_type: Type of questions to generate
            
        Returns:
            List of generated questions
        """
        prompt = f"Generate {num_questions} {question_type} questions based on the following content:\n\n{content}"
        response = await self.generate_content(prompt)
        
        # Split the response into individual questions
        questions = [q.strip() for q in response.split('\n') if q.strip()]
        return questions


# Global instance of the Gemini client
gemini_client = None


async def init_gemini_client():
    """Initialize the Gemini client."""
    global gemini_client
    if settings.google_api_key:  # Only initialize if API key is available
        gemini_client = GeminiClient()