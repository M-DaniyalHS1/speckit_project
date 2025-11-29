"""Hint generation service using Google's Generative AI for the AI-Enhanced Interactive Book Agent."""
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from backend.src.config import settings


class HintGenerator:
    """AI-powered hint generator using Google's Generative AI."""

    def __init__(self):
        """Initialize the hint generator with the AI model."""
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model_name)

    async def generate_hint(
        self,
        content: str,
        query: str,
        hint_level: str = "moderate"
    ) -> str:
        """
        Generate a helpful hint for a given query based on content.

        Args:
            content: The content context for generating the hint
            query: The user's query or problem statement
            hint_level: Level of the hint ("mild", "moderate", "direct")

        Returns:
            Generated hint text
        """
        # Set the hint guidance based on level
        if hint_level == "mild":
            hint_guidance = "Provide a subtle hint that guides thinking without revealing much."
        elif hint_level == "direct":
            hint_guidance = "Provide a direct hint that gives away a significant part of the answer."
        else:  # moderate
            hint_guidance = "Provide a moderate hint that nudges in the right direction without fully revealing the answer."

        prompt = f"""
        {hint_guidance}

        Content: {content}

        User Query: {query}

        Hint:
        """

        try:
            # Generate content using the AI model
            response = await self.model.generate_content_async(prompt)

            # Extract and return the hint
            hint = response.text if response.text else "Sorry, I couldn't generate a hint for that query."

            return hint

        except Exception as e:
            print(f"Error generating hint: {str(e)}")
            return f"Error: Could not generate hint due to an issue with the AI service - {str(e)}"

    async def generate_step_by_step_solution(
        self,
        content: str,
        problem: str,
        solution_steps: int = 3
    ) -> List[Dict[str, str]]:
        """
        Generate a step-by-step breakdown of how to approach a problem.

        Args:
            content: The content context relevant to the problem
            problem: The problem the user is trying to solve
            solution_steps: Number of steps to break the solution into

        Returns:
            List of dictionary objects containing step-by-step instructions
        """
        prompt = f"""
        Break down the solution to the following problem into {solution_steps} clear steps.
        Use the following content as context:

        Content: {content}

        Problem: {problem}

        Provide the solution in the following format:
        {{
            "steps": [
                {{
                    "step": 1,
                    "title": "Step 1 Title",
                    "description": "Detailed description of what to do in this step",
                    "hint": "A helpful hint for this step",
                    "tip": "Any additional tip for this step"
                }}
            ]
        }}

        Make sure to base the steps on the provided content and keep explanations clear and concise.
        """

        try:
            # Generate content using the AI model
            response = await self.model.generate_content_async(prompt)

            import json
            import re

            # Extract JSON from response if it contains it
            response_text = response.text
            
            # Look for JSON format in response
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group()
                try:
                    parsed_data = json.loads(json_str)
                    if "steps" in parsed_data:
                        # Ensure proper formatting of steps
                        formatted_steps = []
                        for step in parsed_data["steps"]:
                            formatted_step = {
                                "step": step.get("step", 1),
                                "title": step.get("title", "Solution Step"),
                                "description": step.get("description", "No description provided"),
                                "hint": step.get("hint", "No specific hint"),
                                "tip": step.get("tip", "No additional tips")
                            }
                            formatted_steps.append(formatted_step)
                        return formatted_steps
                except json.JSONDecodeError:
                    pass

            # If no JSON found, fall back to simple parsing
            steps = []
            lines = response_text.split('\n')
            
            step_counter = 1
            for line in lines:
                if line.strip() and ('step' in line.lower() or str(step_counter) in line):
                    steps.append({
                        "step": step_counter,
                        "title": f"Step {step_counter}",
                        "description": line.replace(f"Step {step_counter}:", "").strip(),
                        "hint": "Review the provided content for relevant information",
                        "tip": f"Take your time with Step {step_counter}"
                    })
                    step_counter += 1
                    if step_counter > solution_steps:
                        break

            # If still no steps were extracted, create a generic response
            if not steps:
                for i in range(1, solution_steps + 1):
                    steps.append({
                        "step": i,
                        "title": f"Solution Step {i}",
                        "description": f"Consider what you know about the problem from the content provided. Think about how previous examples might apply to this situation.",
                        "hint": f"Review the content near where this topic is discussed for guidance on Step {i}",
                        "tip": f"Break down the problem into smaller parts to make Step {i} more manageable"
                    })

            return steps

        except Exception as e:
            print(f"Error generating step-by-step solution: {str(e)}")
            # Return a fallback solution
            fallback_steps = []
            for i in range(1, solution_steps + 1):
                fallback_steps.append({
                    "step": i,
                    "title": f"Step {i}",
                    "description": f"This is a general step for solving the problem based on the content provided. Review the relevant sections carefully.",
                    "hint": "Consult the content provided in the problem context for guidance",
                    "tip": f"Take your time with this step and make sure you understand the underlying concepts"
                })
            return fallback_steps

    async def generate_scaffolding_hints(
        self,
        content: str,
        query: str,
        scaffolding_level: int = 1
    ) -> List[str]:
        """
        Generate a series of hints with increasing levels of directness.

        Args:
            content: The content context for generating hints
            query: The user's query or problem
            scaffolding_level: How many increasingly direct hints to generate (1-3)

        Returns:
            List of progressively more direct hints
        """
        hints = []
        
        for level in range(1, scaffolding_level + 1):
            if level == 1:
                hint_level = "mild"
                guidance = "Provide a very general hint that doesn't reveal specifics."
            elif level == 2:
                hint_level = "moderate"
                guidance = "Provide a more specific hint that gives some direction."
            else:  # level 3
                hint_level = "direct"
                guidance = "Provide a direct hint that gives most of the answer."
            
            prompt = f"""
            {guidance}

            Content: {content}

            Query: {query}

            Hint:
            """

            try:
                response = await self.model.generate_content_async(prompt)
                hint = response.text if response.text else f"Hint level {level} unavailable"
                hints.append(hint)
            except Exception as e:
                print(f"Error generating hint level {level}: {str(e)}")
                hints.append(f"Error generating hint level {level}: {str(e)}")
        
        return hints

    async def generate_metacognitive_hint(
        self,
        content: str,
        query: str
    ) -> str:
        """
        Generate a metacognitive hint that helps the user think about their thinking.

        Args:
            content: The content context
            query: The user's question or problem

        Returns:
            Hint that encourages reflection on problem-solving approaches
        """
        prompt = f"""
        Generate a metacognitive hint that helps the user think about their thinking process.
        Instead of directly answering the question, guide the user to reflect on how they might approach solving this.

        Content: {content}

        Query: {query}

        Metacognitive Hint:
        """

        try:
            response = await self.model.generate_content_async(prompt)
            return response.text if response.text else "Consider reflecting on your problem-solving approach and how the concepts in the content might apply."
        except Exception as e:
            print(f"Error generating metacognitive hint: {str(e)}")
            return "Error generating metacognitive hint. Try reflecting on the problem-solving strategies you know."

    async def generate_general_hint(self, query: str) -> str:
        """
        Generate a general hint for a user's question when specific context is not available.

        Args:
            query: The user's question or problem statement

        Returns:
            General advice or hint for approaching the problem
        """
        prompt = f"""
        Provide a general hint or advice for the following question. 
        Since specific content context is not provided, offer general problem-solving strategies or study tips.

        Query: {query}

        General Hint:
        """

        try:
            response = await self.model.generate_content_async(prompt)
            return response.text if response.text else "Try breaking down the problem into smaller parts and reviewing your study materials."
        except Exception as e:
            print(f"Error generating general hint: {str(e)}")
            return "Error generating general hint. Consider consulting your course materials or asking for more specific guidance."

    async def generate_topic_connection_hint(
        self,
        content: str,
        current_topic: str,
        related_topic: str
    ) -> str:
        """
        Generate a hint that connects two related topics to deepen understanding.

        Args:
            content: The content context that may relate the topics
            current_topic: The topic the user is currently studying
            related_topic: A related topic that could provide insight

        Returns:
            A hint that helps the user see connections between topics
        """
        prompt = f"""
        Generate a hint that helps the user see a connection between '{current_topic}' and '{related_topic}'.
        Use the following content for reference if helpful:
        
        Content: {content}

        Connection Hint:
        """

        try:
            response = await self.model.generate_content_async(prompt)
            return response.text if response.text else f"Think about how '{current_topic}' relates to '{related_topic}'. Both topics often appear together in the content."
        except Exception as e:
            print(f"Error generating topic connection hint: {str(e)}")
            return f"Error generating connection hint. Try to think about how '{current_topic}' and '{related_topic}' might be related."