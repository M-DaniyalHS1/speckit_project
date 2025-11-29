"""Content summarization service using Google's Generative AI for the AI-Enhanced Interactive Book Agent."""
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from backend.src.config import settings


class Summarizer:
    """AI-powered summarization service using Google's Generative AI."""

    def __init__(self):
        """Initialize the summarizer with the AI model."""
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model_name)

    async def generate_summary(
        self,
        content: str,
        summary_type: str = "concise",
        target_length: Optional[int] = None,
        focus_areas: Optional[List[str]] = None
    ) -> str:
        """
        Generate a summary of the given content.

        Args:
            content: The content to summarize
            summary_type: Type of summary to generate ("concise", "detailed", "bullet_points", "key_points")
            target_length: Optional target length for the summary (in words)
            focus_areas: Optional specific topics/concepts to focus on

        Returns:
            Generated summary text
        """
        # Construct the prompt based on summary type
        if summary_type == "concise":
            prompt_instruction = "Provide a concise, clear summary of the main points."
        elif summary_type == "detailed":
            prompt_instruction = "Provide a comprehensive summary covering all important aspects in detail."
        elif summary_type == "bullet_points":
            prompt_instruction = "Provide a bulleted list of key points."
        elif summary_type == "key_points":
            prompt_instruction = "Extract and summarize only the most important key points."
        else:
            prompt_instruction = "Provide a clear summary of the main points."

        # Add focus areas if specified
        focus_instruction = ""
        if focus_areas:
            focus_instruction = f"Focus specifically on these areas: {', '.join(focus_areas)}. "

        # Add target length if specified
        length_instruction = ""
        if target_length:
            length_instruction = f"Keep the summary approximately {target_length} words. "

        # Construct the full prompt
        prompt = f"""
        {prompt_instruction}
        {focus_instruction}
        {length_instruction}

        Content to summarize:
        {content}

        Summary:
        """

        try:
            # Generate content using the AI model
            response = await self.model.generate_content_async(prompt)

            # Extract and return the summary text
            summary = response.text if response.text else "Unable to generate summary for the provided content."

            return summary

        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return f"Error: Unable to generate summary due to an issue with the AI service - {str(e)}"

    async def generate_chapter_summary(
        self,
        chapter_content: str,
        chapter_title: str = "",
        include_key_terms: bool = True,
        summary_length: str = "medium"
    ) -> Dict[str, Any]:
        """
        Generate a chapter-level summary with specific enhancements.

        Args:
            chapter_content: The content of the chapter to summarize
            chapter_title: Title of the chapter (optional)
            include_key_terms: Whether to include important terminology
            summary_length: Length of the summary ("short", "medium", "long")

        Returns:
            Dictionary containing the summary and additional metadata
        """
        # Determine target length based on parameter
        if summary_length == "short":
            length_desc = "short summary with main points only"
            target_length = "under 100 words"
        elif summary_length == "long":
            length_desc = "detailed summary covering all sections"
            target_length = "200-400 words"
        else:  # medium
            length_desc = "balanced summary of key points"
            target_length = "100-200 words"

        # Construct the prompt for chapter summary
        prompt = f"""
        Create a {length_desc} of the following chapter:

        Chapter Title: {chapter_title or 'Untitled Chapter'}

        Chapter Content:
        {chapter_content}

        Requirements:
        1. Provide the main summary
        2. Identify 3-5 key terms/concepts from the chapter
        3. Mention the most important takeaway

        Format:
        SUMMARY: [Your summary here ({target_length})]
        KEY_TERMS: [Term 1], [Term 2], [Term 3]
        MAIN_TAKEAWAY: [Most important point]
        """

        try:
            response = await self.model.generate_content_async(prompt)

            # Parse the response to extract different components
            response_text = response.text

            # Extract summary
            summary_match = response_text.find("SUMMARY:")
            if summary_match != -1:
                summary_start = summary_match + len("SUMMARY:")
                # Find the next section or end of text
                next_section = response_text.find("KEY_TERMS:", summary_start)
                if next_section == -1:
                    next_section = response_text.find("MAIN_TAKEAWAY:", summary_start)
                if next_section == -1:
                    next_section = len(response_text)
                
                summary = response_text[summary_start:next_section].strip()
            else:
                # If the format isn't as expected, return the whole response as summary
                summary = response_text

            # Extract key terms (simplified approach)
            key_terms = []
            terms_match = response_text.find("KEY_TERMS:")
            if terms_match != -1:
                terms_start = terms_match + len("KEY_TERMS:")
                take_away_match = response_text.find("MAIN_TAKEAWAY:", terms_start)
                if take_away_match == -1:
                    terms_end = len(response_text)
                else:
                    terms_end = take_away_match
                terms_section = response_text[terms_start:terms_end].strip()
                # Extract terms from the format [Term1], [Term2], etc.
                import re
                key_terms = re.findall(r'\[(.*?)\]', terms_section)

            # Extract main takeaway
            main_takeaway = ""
            takeaway_match = response_text.find("MAIN_TAKEAWAY:")
            if takeaway_match != -1:
                takeaway_start = takeaway_match + len("MAIN_TAKEAWAY:")
                main_takeaway = response_text[takeaway_start:].strip()

            # Return structured result
            return {
                "chapter_title": chapter_title,
                "summary": summary,
                "key_terms": key_terms,
                "main_takeaway": main_takeaway,
                "summary_length": summary_length,
                "generated_at": __import__('datetime').datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error generating chapter summary: {str(e)}")
            return {
                "chapter_title": chapter_title,
                "summary": f"Error: Unable to generate chapter summary - {str(e)}",
                "key_terms": [],
                "main_takeaway": "",
                "summary_length": summary_length,
                "generated_at": __import__('datetime').datetime.now().isoformat()
            }

    async def generate_custom_summary(
        self,
        content: str,
        summary_purpose: str,
        audience_level: str = "intermediate",
        additional_instructions: Optional[str] = None
    ) -> str:
        """
        Generate a custom-tailored summary based on specific requirements.

        Args:
            content: The content to summarize
            summary_purpose: Purpose of the summary (e.g., "study guide", "quick review", "presentation prep")
            audience_level: Level of the target audience ("beginner", "intermediate", "advanced")
            additional_instructions: Any additional instructions for the summary

        Returns:
            Custom-generated summary text
        """
        # Construct the prompt with customization
        prompt = f"""
        Create a summary for the following content tailored for a {audience_level} audience.
        The purpose of this summary is: {summary_purpose}.

        Content:
        {content}

        Additional Instructions:
        {additional_instructions or 'No additional instructions provided.'}

        Provide the summary below:
        """

        try:
            response = await self.model.generate_content_async(prompt)
            
            summary = response.text if response.text else "Unable to generate summary based on the provided instructions."
            
            return summary

        except Exception as e:
            print(f"Error generating custom summary: {str(e)}")
            return f"Error: Unable to generate custom summary - {str(e)}"

    async def generate_multi_document_summary(
        self,
        documents: List[Dict[str, str]],
        comparison_needed: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a summary across multiple related documents.

        Args:
            documents: List of documents, each with "title" and "content" fields
            comparison_needed: Whether to highlight similarities and differences across documents

        Returns:
            Dictionary containing summary of all documents with optional comparison
        """
        if not documents:
            return {"error": "No documents provided for multi-document summary"}

        # Format the documents for the prompt
        formatted_docs = []
        for i, doc in enumerate(documents):
            title = doc.get("title", f"Document {i+1}")
            content = doc.get("content", "")
            formatted_docs.append(f"Document {i+1} - {title}:\n{content}\n\n")

        if comparison_needed:
            prompt = f"""
            Analyze the following related documents and provide:
            1. Individual summaries of each document
            2. Comparison highlighting similarities and differences across documents
            3. Overall synthesis of key themes

            Documents:
            {''.join(formatted_docs)}

            Response format:
            DOCUMENT_SUMMARIES: [Individual summaries]
            COMPARISON_HIGHLIGHTS: [Similarities and differences]
            OVERALL_SYNTHESIS: [Synthesis of key themes]
            """
        else:
            prompt = f"""
            Generate a comprehensive summary that encompasses all of the following related documents:

            Documents:
            {''.join(formatted_docs)}

            Provide an integrated summary that captures the key points from all documents.
            """

        try:
            response = await self.model.generate_content_async(prompt)

            response_text = response.text

            if comparison_needed:
                # Attempt to parse the structured response
                doc_summaries_match = response_text.find("DOCUMENT_SUMMARIES:")
                comparison_match = response_text.find("COMPARISON_HIGHLIGHTS:")
                synthesis_match = response_text.find("OVERALL_SYNTHESIS:")

                doc_summaries = ""
                comparison_highlights = ""
                overall_synthesis = ""

                if doc_summaries_match != -1:
                    start = doc_summaries_match + len("DOCUMENT_SUMMARIES:")
                    end = comparison_match if comparison_match != -1 else synthesis_match if synthesis_match != -1 else len(response_text)
                    doc_summaries = response_text[start:end].strip()

                if comparison_match != -1:
                    start = comparison_match + len("COMPARISON_HIGHLIGHTS:")
                    end = synthesis_match if synthesis_match != -1 else len(response_text)
                    comparison_highlights = response_text[start:end].strip()

                if synthesis_match != -1:
                    start = synthesis_match + len("OVERALL_SYNTHESIS:")
                    overall_synthesis = response_text[start:].strip()

                return {
                    "document_summaries": doc_summaries if doc_summaries else response_text,
                    "comparison_highlights": comparison_highlights,
                    "overall_synthesis": overall_synthesis,
                    "document_count": len(documents)
                }
            else:
                return {
                    "summary": response_text,
                    "document_count": len(documents)
                }

        except Exception as e:
            print(f"Error generating multi-document summary: {str(e)}")
            return {
                "error": f"Unable to generate multi-document summary: {str(e)}",
                "document_count": len(documents)
            }