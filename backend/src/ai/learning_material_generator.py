"""AI learning material generator for the AI-Enhanced Interactive Book Agent."""
import google.generativeai as genai
from backend.src.config import settings


class LearningMaterialGenerator:
    """AI-powered learning material generator using Google's Generative AI."""
    
    def __init__(self):
        """Initialize the learning material generator with the AI model."""
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model_name)
    
    async def generate_quiz(self, content: str, num_questions: int = 5) -> list:
        """
        Generate quiz questions based on the given content.
        
        Args:
            content: The book content to generate quiz questions from
            num_questions: Number of questions to generate
            
        Returns:
            List of quiz questions
        """
        prompt = f"""
        Based on the following content, generate {num_questions} quiz questions with multiple choice answers:
        
        Content: {content}
        
        For each question:
        1. Provide the question
        2. Give 4 answer options (A, B, C, D)
        3. Indicate the correct answer
        
        Format each question as follows:
        Question: [question text]
        A) [option A]
        B) [option B]
        C) [option C]
        D) [option D]
        Correct Answer: [A/B/C/D]
        """
        
        # Generate the quiz using the AI model
        response = await self.model.generate_content_async(prompt)
        
        # Return the generated text as a list (in a real implementation, 
        # you'd parse the response into structured quiz questions)
        if response.text:
            return [response.text]
        else:
            return ["I'm sorry, I couldn't generate quiz questions for that content."]
    
    async def generate_flashcards(self, content: str) -> list:
        """
        Generate flashcards based on the given content.
        
        Args:
            content: The book content to generate flashcards from
            
        Returns:
            List of flashcards (question/answer pairs)
        """
        prompt = f"""
        Based on the following content, generate flashcards with questions and answers:
        
        Content: {content}
        
        Create flashcards in the format:
        Front: [question/prompt]
        Back: [answer/definition]
        
        Generate at least 5 flashcards focusing on the key concepts, terms, and important information.
        """
        
        # Generate the flashcards using the AI model
        response = await self.model.generate_content_async(prompt)
        
        # Return the generated text as a list (in a real implementation, 
        # you'd parse the response into structured flashcards)
        if response.text:
            return [response.text]
        else:
            return ["I'm sorry, I couldn't generate flashcards for that content."]
    
    async def generate_notes(self, content: str) -> str:
        """
        Generate structured notes based on the given content.
        
        Args:
            content: The book content to generate notes from
            
        Returns:
            Structured notes
        """
        prompt = f"""
        Create structured notes from the following content:
        
        Content: {content}
        
        Organize the notes with:
        1. Main headings for major topics
        2. Bullet points for key concepts
        3. Important definitions or terms
        4. Key takeaways or summary points
        """
        
        # Generate the notes using the AI model
        response = await self.model.generate_content_async(prompt)
        
        # Return the generated text
        return response.text if response.text else "I'm sorry, I couldn't generate notes for that content."