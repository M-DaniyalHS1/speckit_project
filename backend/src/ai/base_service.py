"""Base AI service class for the AI-Enhanced Interactive Book Agent.

This module provides a base class for all AI-powered services in the application,
implementing common functionality like rate limiting, error handling, and
fallback mechanisms.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from backend.src.ai.gemini_client import gemini_client
from backend.src.config import settings
import asyncio
import time
import logging


class AIServiceBase(ABC):
    """Base class for AI services implementing common functionality."""
    
    def __init__(self):
        """Initialize the AI service with required components."""
        if gemini_client is None:
            raise ValueError("Gemini client must be initialized before creating AI services")
        
        # Initialize rate limiting
        self._requests_made = []
        self._rate_limit_window = 60  # seconds
        self._max_requests_per_minute = settings.api_rate_limit  # Use configured rate limit
        
        # Set up logging
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _check_rate_limit(self) -> bool:
        """Check if the service is within rate limits.
        
        Returns:
            True if within limits, False otherwise
        """
        # Clean old requests outside the time window
        current_time = time.time()
        self._requests_made = [
            req_time for req_time in self._requests_made
            if current_time - req_time < self._rate_limit_window
        ]
        
        # Check if we're within the limit
        if len(self._requests_made) >= self._max_requests_per_minute:
            return False
        
        # Add current request to the list
        self._requests_made.append(current_time)
        return True
    
    async def _with_fallback(self, primary_func, fallback_func, *args, **kwargs) -> Any:
        """Execute a primary function with a fallback if it fails.
        
        Args:
            primary_func: The primary function to execute
            fallback_func: The fallback function to execute if primary fails
            *args: Arguments to pass to the functions
            **kwargs: Keyword arguments to pass to the functions
            
        Returns:
            Result from either primary or fallback function
        """
        try:
            # Check rate limit before making request
            if not self._check_rate_limit():
                self.logger.warning("Rate limit exceeded, using fallback")
                return await fallback_func(*args, **kwargs)
            
            result = await primary_func(*args, **kwargs)
            return result
        except Exception as e:
            self.logger.error(f"Primary AI service failed: {str(e)}, trying fallback")
            return await fallback_func(*args, **kwargs)
    
    @abstractmethod
    async def process(self, *args, **kwargs) -> Any:
        """Process the input using AI capabilities.
        
        This method should be implemented by subclasses.
        
        Args:
            *args: Arguments for processing
            **kwargs: Keyword arguments for processing
            
        Returns:
            Processed result
        """
        pass


class ContentExtractionService(AIServiceBase):
    """Service for extracting content from various sources."""
    
    async def process(self, content: str, extraction_type: str = "key_points") -> List[str]:
        """Extract specific information from content.
        
        Args:
            content: The content to extract information from
            extraction_type: Type of extraction to perform (key_points, entities, etc.)
            
        Returns:
            List of extracted information
        """
        async def primary_extraction():
            prompt = f"Extract {extraction_type} from the following text:\n\n{content}"
            result = await gemini_client.generate_content(prompt)
            # Parse the result into a list
            items = [item.strip() for item in result.split('\n') if item.strip()]
            return items
        
        async def fallback_extraction():
            # Simple fallback that just returns the first few sentences
            sentences = content.split('. ')
            return sentences[:5]  # Return first 5 sentences as key points
        
        return await self._with_fallback(primary_extraction, fallback_extraction)


class ContentAnalysisService(AIServiceBase):
    """Service for analyzing content for various purposes."""
    
    async def process(
        self, 
        content: str, 
        analysis_type: str = "sentiment", 
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze content for specific characteristics.
        
        Args:
            content: The content to analyze
            analysis_type: Type of analysis to perform
            context: Additional context for the analysis
            
        Returns:
            Dictionary containing analysis results
        """
        async def primary_analysis():
            prompt = f"Perform {analysis_type} analysis on the following text:\n\n{content}"
            if context:
                prompt += f"\n\nContext: {context}"
            
            result = await gemini_client.generate_content(prompt)
            # For now, just return the raw result - in a real implementation
            # we'd parse this into structured data
            return {"analysis": result, "type": analysis_type}
        
        async def fallback_analysis():
            return {
                "analysis": f"Unable to perform {analysis_type} analysis. Content too complex for fallback.",
                "type": analysis_type,
                "fallback": True
            }
        
        return await self._with_fallback(primary_analysis, fallback_analysis)


class ContentGenerationService(AIServiceBase):
    """Service for generating content based on prompts."""
    
    async def process(
        self, 
        prompt: str, 
        context: Optional[str] = None,
        content_type: str = "text"
    ) -> str:
        """Generate content based on the prompt and context.
        
        Args:
            prompt: The prompt to guide content generation
            context: Additional context for generation
            content_type: Type of content to generate
            
        Returns:
            Generated content
        """
        async def primary_generation():
            return await gemini_client.generate_content(
                prompt=prompt,
                context=context,
                temperature=0.7
            )
        
        async def fallback_generation():
            return f"Unable to generate {content_type} content. Fallback response for: {prompt[:50]}..."
        
        return await self._with_fallback(primary_generation, fallback_generation)


class EmbeddingService(AIServiceBase):
    """Service for generating embeddings from text."""
    
    async def process(self, text: str) -> List[float]:
        """Generate embeddings for the given text.
        
        Args:
            text: Text to generate embeddings for
            
        Returns:
            List of embedding values
        """
        async def primary_embedding():
            return await gemini_client.embed_content(text)
        
        async def fallback_embedding():
            # Simple fallback: return a hash-based pseudo-embedding
            # This is not a real embedding but maintains the interface
            text_hash = hash(text)
            embedding = [float((text_hash >> i) & 0xFF) / 255.0 for i in range(0, 768, 8)]  # 96 dimensions
            return embedding[:768]  # Standard size for embeddings
        
        return await self._with_fallback(primary_embedding, fallback_embedding)