"""AI explanation generator for the AI-Enhanced Interactive Book Agent."""
import google.generativeai as genai
from backend.src.config import settings


class ExplanationGenerator:
    """AI-powered explanation generator using Google's Generative AI."""
    
    def __init__(self):
        """Initialize the explanation generator with the AI model."""
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model_name)
    
    async def generate_explanation(
        self, 
        content: str, 
        query: str, 
        complexity_level: str = "simple"
    ) -> str:
        """
        Generate an explanation for the given content and query.
        
        Args:
            content: The book content to explain
            query: The specific query about the content
            complexity_level: How complex the explanation should be ("simple", "detailed", "technical")
            
        Returns:
            Generated explanation text
        """
        # Construct the prompt based on complexity level
        if complexity_level == "simple":
            prompt = f"""
            Explain the following content in simple terms that are easy to understand:
            
            Content: {content}
            
            User's question: {query}
            
            Please provide a clear, concise explanation using simple language that someone with basic knowledge can understand.
            """
        elif complexity_level == "detailed":
            prompt = f"""
            Provide a detailed explanation of the following content:
            
            Content: {content}
            
            User's question: {query}
            
            Please provide a comprehensive explanation that covers multiple aspects of the topic, with examples and deeper insights.
            """
        elif complexity_level == "technical":
            prompt = f"""
            Provide a technical explanation of the following content:
            
            Content: {content}
            
            User's question: {query}
            
            Please provide a technical explanation using specialized terminology and detailed analysis appropriate for experts in the field.
            """
        else:
            prompt = f"""
            Explain the following content:
            
            Content: {content}
            
            User's question: {query}
            
            Please provide a clear explanation.
            """
        
        # Generate the explanation using the AI model
        response = await self.model.generate_content_async(prompt)
        
        # Return the generated text
        return response.text if response.text else "I'm sorry, I couldn't generate an explanation for that content."