"""RAG ingestion package."""

from .loaders import load_document, get_loader
from .chunker import chunk_document, SemanticChunker
from .metadata import create_metadata, MetadataManager

__all__ = [
    'load_document',
    'get_loader',
    'chunk_document',
    'SemanticChunker',
    'create_metadata',
    'MetadataManager',
]
