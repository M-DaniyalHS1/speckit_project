"""Question generation service using Google's Generative AI for the AI-Enhanced Interactive Book Agent."""
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from backend.src.config import settings


class QuestionGenerator:
    """AI-powered question generator using Google's Generative AI."""

    def __init__(self):
        """Initialize the question generator with the AI model."""
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model_name)

    async def generate_questions(
        self,
        content: str,
        num_questions: int = 5,
        question_type: str = "multiple_choice",
        difficulty: str = "medium"
    ) -> List[Dict[str, Any]]:
        """
        Generate questions based on the provided content.

        Args:
            content: The content to generate questions from
            num_questions: Number of questions to generate
            question_type: Type of questions to generate (multiple_choice, short_answer, true_false, etc.)
            difficulty: Difficulty level of questions (easy, medium, hard)

        Returns:
            List of generated questions with possible answers and explanations
        """
        # Construct the prompt based on parameters
        prompt = f"""
        Generate {num_questions} {difficulty} {question_type} questions based on the following content:

        {content}

        For each question, provide:
        1. The question text
        2. Answer options if it's a multiple-choice question (otherwise just the answer)
        3. Correct answer
        4. Brief explanation of why it's correct
        5. Difficulty level

        Format the response as JSON with the following structure:
        {{
          "questions": [
            {{
              "question": "...",
              "options": ["...", "...", "...", "..."], // Only for multiple choice
              "answer": "...",
              "explanation": "...",
              "difficulty": "{difficulty}"
            }}
          ]
        }}
        """

        try:
            # Generate content using the AI model
            response = await self.model.generate_content_async(prompt)

            # Parse the response to extract questions
            import json
            import re

            # Extract JSON from response if it contains it
            response_text = response.text
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)

            if json_match:
                json_str = json_match.group()
                parsed_data = json.loads(json_str)
                
                if "questions" in parsed_data:
                    return parsed_data["questions"]
                else:
                    # If the response doesn't have the expected structure, return a single question
                    return [{
                        "question": f"Based on the content: {response_text[:100]}...",
                        "answer": "See content above",
                        "explanation": "Auto-generated question based on provided content",
                        "difficulty": difficulty
                    }]
            else:
                # If no JSON found, return a basic structure
                return [{
                    "question": f"Based on the content: {response_text[:100]}...",
                    "answer": "See content above",
                    "explanation": "Auto-generated question based on provided content",
                    "difficulty": difficulty
                }]

        except Exception as e:
            print(f"Error generating questions: {str(e)}")
            # Return a fallback response
            return [{
                "question": f"Review the content: {content[:100]}...",
                "answer": "Based on the content covered",
                "explanation": "AI question generation failed, please review the content",
                "difficulty": difficulty
            }]

    async def generate_questions_and_answers(
        self,
        content: str,
        count: int = 5
    ) -> List[Dict[str, str]]:
        """
        Generate question-answer pairs from content.
        
        Args:
            content: The content to generate Q&A from
            count: Number of Q&A pairs to generate
        
        Returns:
            List of dictionaries containing question and answer
        """
        # Generate a mix of different types of questions
        questions_data = await self.generate_questions(
            content=content,
            num_questions=count,
            question_type="mixed",
            difficulty="medium"
        )
        
        # Extract just question and answer pairs
        qa_pairs = []
        for item in questions_data:
            qa_pairs.append({
                "question": item.get("question", "No question generated"),
                "answer": item.get("answer", "No answer provided"),
                "explanation": item.get("explanation", "No explanation provided"),
                "difficulty": item.get("difficulty", "medium")
            })
        
        return qa_pairs

    async def generate_study_questions(
        self,
        content: str,
        focus_area: Optional[str] = None,
        num_questions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate study-focused questions for educational purposes.

        Args:
            content: The content to generate questions from
            focus_area: Specific area or concept to focus questions on (optional)
            num_questions: Number of questions to generate

        Returns:
            List of study-focused questions with detailed explanations
        """
        focus_instruction = f"with a focus on {focus_area}" if focus_area else "covering key concepts"
        
        prompt = f"""
        Generate {num_questions} in-depth study questions from the following content {focus_instruction}:

        {content}

        Each question should:
        - Test understanding of core concepts
        - Require analysis or synthesis of information
        - Have a clear, well-reasoned answer
        - Include a detailed explanation of why the answer is correct
        - Be appropriate for self-study or classroom use

        Provide the results in JSON format with the following structure:
        {{
          "study_questions": [
            {{
              "question": "...",
              "answer": "...",
              "explanation": "...",
              "key_concepts": ["concept1", "concept2"],
              "difficulty": "medium"
            }}
          ]
        }}
        """

        try:
            response = await self.model.generate_content_async(prompt)
            
            import json
            import re
            
            # Extract JSON from response
            response_text = response.text
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group()
                parsed_data = json.loads(json_str)
                
                if "study_questions" in parsed_data:
                    return parsed_data["study_questions"]
            
            # Fallback: return basic question format
            return [{
                "question": f"Analyze this content: {content[:150]}...",
                "answer": "This requires careful analysis of the provided content",
                "explanation": "This question requires synthesizing information from the provided content",
                "key_concepts": ["comprehension", "analysis"],
                "difficulty": "medium"
            } for _ in range(num_questions)]
            
        except Exception as e:
            print(f"Error generating study questions: {str(e)}")
            return [{
                "question": f"Study question based on: {content[:100]}...",
                "answer": "See content for detailed understanding",
                "explanation": "Review the content thoroughly",
                "key_concepts": ["review"],
                "difficulty": "medium"
            } for _ in range(num_questions)]

    async def generate_quiz(
        self,
        content: str,
        num_questions: int = 10,
        difficulty_distribution: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete quiz with a specific distribution of difficulty levels.

        Args:
            content: The content to generate quiz from
            num_questions: Total number of questions in the quiz
            difficulty_distribution: Distribution of difficulty levels (e.g., {"easy": 0.3, "medium": 0.5, "hard": 0.2})

        Returns:
            Dictionary containing the quiz with questions and metadata
        """
        if difficulty_distribution is None:
            difficulty_distribution = {"easy": 0.3, "medium": 0.5, "hard": 0.2}
        
        quiz = {
            "title": f"Quiz: Content Review ({num_questions} questions)",
            "description": "Auto-generated quiz based on provided content",
            "total_questions": num_questions,
            "content_summary": content[:100] + "..." if len(content) > 100 else content,
            "questions": []
        }
        
        # Calculate number of questions per difficulty level
        questions_per_difficulty = {}
        remaining_questions = num_questions
        
        for difficulty, ratio in difficulty_distribution.items():
            num_for_difficulty = int(num_questions * ratio)
            questions_per_difficulty[difficulty] = num_for_difficulty
            remaining_questions -= num_for_difficulty
        
        # Distribute remaining questions to the first difficulty level
        if remaining_questions > 0:
            first_difficulty = list(difficulty_distribution.keys())[0]
            questions_per_difficulty[first_difficulty] += remaining_questions
        
        # Generate questions for each difficulty level
        for difficulty, count in questions_per_difficulty.items():
            if count > 0:
                questions = await self.generate_questions(
                    content=content,
                    num_questions=min(count, num_questions),  # Don't exceed total requested
                    question_type="mixed",
                    difficulty=difficulty
                )
                quiz["questions"].extend(questions)
        
        # Randomly shuffle questions
        import random
        random.shuffle(quiz["questions"])
        
        # Trim to exact number requested
        quiz["questions"] = quiz["questions"][:num_questions]
        quiz["total_questions"] = len(quiz["questions"])
        
        return quiz