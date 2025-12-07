"""Semantic document chunking for RAG."""

import re
from typing import List, Dict, Any
import tiktoken


class SemanticChunker:
    """Chunks documents semantically by paragraphs/sections."""
    
    def __init__(self, max_tokens: int = 1000, overlap_tokens: int = 100):
        """
        Initialize chunker.
        
        Args:
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Number of tokens to overlap between chunks
        """
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk text into semantic chunks.
        
        Args:
            text: Text to chunk
            metadata: Base metadata to attach to each chunk
            
        Returns:
            List of chunk dicts with 'content' and 'metadata'
        """
        # Split into paragraphs first
        paragraphs = self._split_paragraphs(text)
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0
        
        for para in paragraphs:
            para_tokens = self._count_tokens(para)
            
            # If single paragraph exceeds max, split it further
            if para_tokens > self.max_tokens:
                # Finish current chunk if any
                if current_chunk:
                    chunks.append(self._create_chunk(
                        current_chunk, metadata, chunk_index
                    ))
                    chunk_index += 1
                    current_chunk = []
                    current_tokens = 0
                
                # Split large paragraph by sentences
                sub_chunks = self._split_large_paragraph(para, metadata, chunk_index)
                chunks.extend(sub_chunks)
                chunk_index += len(sub_chunks)
                
            elif current_tokens + para_tokens > self.max_tokens:
                # Current chunk is full, save it
                chunks.append(self._create_chunk(
                    current_chunk, metadata, chunk_index
                ))
                chunk_index += 1
                
                # Start new chunk with overlap
                current_chunk = [para]
                current_tokens = para_tokens
            else:
                # Add to current chunk
                current_chunk.append(para)
                current_tokens += para_tokens
        
        # Save remaining chunk
        if current_chunk:
            chunks.append(self._create_chunk(
                current_chunk, metadata, chunk_index
            ))
        
        return chunks
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split on double newlines, headers, or list items
        paragraphs = re.split(r'\n\s*\n+', text)
        
        # Clean and filter empty
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def _split_large_paragraph(
        self, 
        paragraph: str, 
        metadata: Dict[str, Any], 
        start_index: int
    ) -> List[Dict[str, Any]]:
        """Split a large paragraph by sentences."""
        # Split by sentence endings
        sentences = re.split(r'([.!?]+\s+)', paragraph)
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = start_index
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            if i + 1 < len(sentences):
                # Include punctuation with sentence
                sentence += sentences[i + 1]
                i += 2
            else:
                i += 1
            
            sentence_tokens = self._count_tokens(sentence)
            
            if current_tokens + sentence_tokens > self.max_tokens:
                if current_chunk:
                    chunks.append(self._create_chunk(
                        current_chunk, metadata, chunk_index
                    ))
                    chunk_index += 1
                current_chunk = [sentence]
                current_tokens = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        if current_chunk:
            chunks.append(self._create_chunk(
                current_chunk, metadata, chunk_index
            ))
        
        return chunks
    
    def _create_chunk(
        self, 
        paragraphs: List[str], 
        base_metadata: Dict[str, Any], 
        chunk_index: int
    ) -> Dict[str, Any]:
        """Create a chunk dict."""
        content = '\n\n'.join(paragraphs)
        
        metadata = base_metadata.copy()
        metadata['chunk_index'] = chunk_index
        metadata['chunk_tokens'] = self._count_tokens(content)
        
        return {
            'content': content,
            'metadata': metadata
        }
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))


def chunk_document(
    content: str, 
    metadata: Dict[str, Any],
    max_tokens: int = 1000,
    overlap_tokens: int = 100
) -> List[Dict[str, Any]]:
    """
    Chunk a document into semantic chunks.
    
    Args:
        content: Document content
        metadata: Document metadata
        max_tokens: Maximum tokens per chunk
        overlap_tokens: Overlap between chunks
        
    Returns:
        List of chunks with content and metadata
    """
    chunker = SemanticChunker(max_tokens, overlap_tokens)
    return chunker.chunk_text(content, metadata)
