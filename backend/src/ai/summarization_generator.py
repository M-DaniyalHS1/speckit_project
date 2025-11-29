"""AI summarization generator for the AI-Enhanced Interactive Book Agent."""
import google.generativeai as genai
from backend.src.config import settings


class SummarizationGenerator:
    """AI-powered summarization generator using Google's Generative AI."""
    
    def __init__(self):
        """Initialize the summarization generator with the AI model."""
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model_name)
    
    async def generate_section_summary(self, content: str) -> str:
        """
        Generate a summary of the given content.
        
        Args:
            content: The book content to summarize
            
        Returns:
            Generated summary text
        """
        prompt = f"""
        Please provide a concise summary of the following content:
        
        Content: {content}
        
        The summary should capture the key points, main ideas, and important details in a clear and organized manner. 
        Keep the summary significantly shorter than the original content while preserving the essential information.
        """
        
        # Generate the summary using the AI model
        response = await self.model.generate_content_async(prompt)
        
        # Return the generated text
        return response.text if response.text else "I'm sorry, I couldn't generate a summary for that content."
    
    async def generate_key_points(self, content: str) -> str:
        """
        Generate key points from the given content.
        
        Args:
            content: The book content to extract key points from
            
        Returns:
            Generated key points text
        """
        prompt = f"""
        Please extract the key points from the following content:
        
        Content: {content}
        
        List the most important points in a clear, bullet-point format. Focus on the main ideas, concepts, and facts.
        """
        
        # Generate the key points using the AI model
        response = await self.model.generate_content_async(prompt)
        
        # Return the generated text
        return response.text if response.text else "I'm sorry, I couldn't extract key points from that content."