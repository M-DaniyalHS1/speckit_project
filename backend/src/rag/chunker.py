"""Text chunking utility for the AI-Enhanced Interactive Book Agent."""
import re
from typing import List, Tuple, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter


class TextChunker:
    """Utility class for splitting text content into manageable chunks for RAG processing."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """Initialize the TextChunker with default or specified parameters.

        Args:
            chunk_size: Maximum size of each chunk (in characters)
            overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Tuple[str, Dict[str, Any]]]:
        """Split text into chunks with associated metadata.

        Args:
            text: Input text to be chunked
            metadata: Base metadata to include with each chunk

        Returns:
            List of tuples containing (chunk_text, chunk_metadata)
        """
        if not text:
            return []

        # Use langchain's text splitter to chunk the text
        chunks = self.text_splitter.split_text(text)

        result = []
        for i, chunk in enumerate(chunks):
            # Create chunk-specific metadata
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                "chunk_id": f"chunk_{i}_{len(chunk)}",
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk),
                "is_first_chunk": i == 0,
                "is_last_chunk": i == len(chunks) - 1
            })

            result.append((chunk, chunk_metadata))

        return result

    def chunk_by_paragraphs(self, text: str, metadata: Dict[str, Any] = None) -> List[Tuple[str, Dict[str, Any]]]:
        """Split text by paragraphs while maintaining size constraints.

        Args:
            text: Input text to be chunked
            metadata: Base metadata to include with each chunk

        Returns:
            List of tuples containing (chunk_text, chunk_metadata)
        """
        # Split by paragraphs (handling various paragraph separators)
        paragraphs = re.split(r'\n\s*\n|\r\n\s*\r\n', text)
        
        result = []
        current_chunk = ""
        current_metadata = metadata.copy() if metadata else {}
        chunk_index = 0
        
        for para_idx, paragraph in enumerate(paragraphs):
            # If adding this paragraph would exceed chunk size, start a new chunk
            if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                result.append((
                    current_chunk.strip(),
                    {**current_metadata, "chunk_id": f"para_chunk_{chunk_index}", "chunk_index": chunk_index}
                ))
                chunk_index += 1
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph

        # Add the final chunk if it has content
        if current_chunk.strip():
            result.append((
                current_chunk.strip(),
                {**current_metadata, "chunk_id": f"para_chunk_{chunk_index}", "chunk_index": chunk_index}
            ))

        return result

    def chunk_by_sections(self, text: str, section_pattern: str = r'^#+\s.*$', 
                         metadata: Dict[str, Any] = None) -> List[Tuple[str, Dict[str, Any]]]:
        """Split text by sections based on a pattern (e.g., headings).

        Args:
            text: Input text to be chunked
            section_pattern: Regex pattern to identify section breaks
            metadata: Base metadata to include with each chunk

        Returns:
            List of tuples containing (chunk_text, chunk_metadata)
        """
        sections = re.split(section_pattern, text, flags=re.MULTILINE)
        headers = re.findall(section_pattern, text, flags=re.MULTILINE)
        
        result = []
        
        for i, (header, section_content) in enumerate(zip(headers, sections[1:])):
            # Combine header with content
            section_text = f"{header}\n\n{section_content}"
            
            # If section is too large, fall back to recursive splitting
            if len(section_text) > self.chunk_size:
                chunk_pairs = self.chunk_text(section_text, metadata)
                for j, (chunk, chunk_meta) in enumerate(chunk_pairs):
                    chunk_meta.update({
                        "section_header": header,
                        "sub_chunk_index": j,
                        "section_chunk": True
                    })
                    result.append((chunk, chunk_meta))
            else:
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    "chunk_id": f"section_chunk_{i}",
                    "chunk_index": i,
                    "section_header": header,
                    "section_chunk": True
                })
                result.append((section_text, chunk_metadata))

        return result

    def get_optimal_chunk_size(self, text: str, target_chunks: int = 10) -> int:
        """Determine an optimal chunk size to achieve a target number of chunks.

        Args:
            text: Input text to analyze
            target_chunks: Desired number of chunks

        Returns:
            Optimal chunk size
        """
        if target_chunks <= 0:
            return self.chunk_size

        text_length = len(text)
        optimal_size = text_length // target_chunks
        
        # Ensure the size is within reasonable bounds
        return max(200, min(optimal_size, 2000))


# Global instance of the text chunker
text_chunker = TextChunker()