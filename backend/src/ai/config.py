"""AI configuration module for the AI-Enhanced Interactive Book Agent.

This module handles configuration for AI services, including API settings,
fallback mechanisms, and model management.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import os
from backend.src.config import settings


@dataclass
class AIModelConfig:
    """Configuration for a specific AI model."""
    name: str
    provider: str
    max_tokens: int
    temperature: float
    fallback_models: List[str]
    enabled: bool = True


@dataclass
class AIApiConfig:
    """Configuration for AI API connections."""
    provider: str
    api_key: str
    base_url: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    rate_limit: int = 10  # requests per minute


class AIConfigManager:
    """Manager for AI configurations and settings."""
    
    def __init__(self):
        """Initialize the AI configuration manager."""
        # Configuration for the primary AI model (Google Gemini)
        self.primary_model = AIModelConfig(
            name=settings.gemini_model_name,
            provider="google",
            max_tokens=1024,
            temperature=0.7,
            fallback_models=["gemini-pro", "gemini-2.0-flash"]  # Fallback models in order of preference
        )
        
        # Configuration for embedding model
        self.embedding_model = AIModelConfig(
            name="models/embedding-001",
            provider="google",
            max_tokens=512,
            temperature=0.0,  # Deterministic for embeddings
            fallback_models=["models/embedding-001"]
        )
        
        # API configuration
        self.api_config = AIApiConfig(
            provider="google",
            api_key=settings.google_api_key,
            timeout=settings.external_api_timeout,
            max_retries=3,
            rate_limit=settings.api_rate_limit
        )
        
        # Model availability status
        self.model_availability: Dict[str, bool] = {}
        
        # Initialize availability status for all models
        self._init_model_availability()
    
    def _init_model_availability(self):
        """Initialize model availability status based on configuration."""
        # Start with all models as available
        all_models = [self.primary_model.name] + self.primary_model.fallback_models + [self.embedding_model.name]
        for model in all_models:
            self.model_availability[model] = True  # Initially assume all models are available
    
    def get_available_model(self, model_config: AIModelConfig) -> str:
        """Get an available model from the config, trying fallbacks if needed.
        
        Args:
            model_config: Configuration for the primary model
            
        Returns:
            Name of an available model
        """
        # If the primary model is available, use it
        if self.model_availability[model_config.name]:
            return model_config.name
        
        # Try fallback models
        for fallback_model in model_config.fallback_models:
            if self.model_availability[fallback_model]:
                return fallback_model
        
        # If no fallbacks available, return the primary model (will likely fail, but follows proper protocol)
        return model_config.name
    
    def mark_model_unavailable(self, model_name: str):
        """Mark a model as unavailable.
        
        Args:
            model_name: Name of the model to mark as unavailable
        """
        self.model_availability[model_name] = False
        print(f"Marked model {model_name} as unavailable")
    
    def mark_model_available(self, model_name: str):
        """Mark a model as available.
        
        Args:
            model_name: Name of the model to mark as available
        """
        self.model_availability[model_name] = True
        print(f"Marked model {model_name} as available")
    
    def get_model_config_by_name(self, model_name: str) -> Optional[AIModelConfig]:
        """Get the configuration for a specific model by name.
        
        Args:
            model_name: Name of the model to get config for
            
        Returns:
            Configuration for the model, or None if not found
        """
        if model_name == self.primary_model.name:
            return self.primary_model
        elif model_name == self.embedding_model.name:
            return self.embedding_model
        else:
            # Check if it's a fallback model
            for model_config in [self.primary_model, self.embedding_model]:
                if model_name in model_config.fallback_models:
                    # Return a modified config for the fallback model
                    return AIModelConfig(
                        name=model_name,
                        provider=model_config.provider,
                        max_tokens=model_config.max_tokens,
                        temperature=model_config.temperature,
                        fallback_models=model_config.fallback_models
                    )
        return None
    
    def get_primary_model_config(self) -> AIModelConfig:
        """Get the configuration for the primary model.
        
        Returns:
            Configuration for the primary model
        """
        return self.primary_model
    
    def get_embedding_model_config(self) -> AIModelConfig:
        """Get the configuration for the embedding model.
        
        Returns:
            Configuration for the embedding model
        """
        return self.embedding_model


# Global instance of the AI configuration manager
ai_config_manager = AIConfigManager()


def get_fallback_response(error_type: str = "general") -> str:
    """Get a fallback response when AI services are unavailable.
    
    Args:
        error_type: Type of error that occurred
        
    Returns:
        Fallback response string
    """
    fallback_responses = {
        "general": "I'm currently unable to process your request. Please try again later.",
        "model_unavailable": "The AI model is temporarily unavailable. Please try again later.",
        "api_error": "There was an issue connecting to the AI service. Please try again later.",
        "rate_limit": "I've reached the limit for AI requests. Please try again shortly.",
        "content_too_long": "The content you requested is too long to process at the moment."
    }
    
    return fallback_responses.get(error_type, fallback_responses["general"])


def validate_api_key(api_key: str) -> bool:
    """Validate if the provided API key is properly formatted.
    
    Args:
        api_key: The API key to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not api_key or len(api_key) < 10:
        return False
    
    # Google API keys typically start with "AI" followed by a string
    # This is a basic check - in a real implementation, we'd have more specific validation
    return True


# Initialize configuration
def init_ai_config():
    """Initialize AI configurations and validate settings."""
    if not validate_api_key(settings.google_api_key):
        raise ValueError("Invalid or missing Google API key")
    
    # Additional initialization could go here
    print("AI Configuration initialized successfully")