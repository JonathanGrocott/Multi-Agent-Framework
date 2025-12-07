"""Metadata management for RAG documents."""

from datetime import datetime
from typing import Dict, Any, Optional


class MetadataManager:
    """Manages document metadata."""
    
    REQUIRED_FIELDS = {'machine_id', 'source_file'}
    OPTIONAL_FIELDS = {'doc_type', 'version', 'author', 'section', 'tags', 'language'}
    
    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> None:
        """
        Validate metadata has required fields.
        
        Raises:
            ValueError: If required fields missing
        """
        missing = MetadataManager.REQUIRED_FIELDS - set(metadata.keys())
        if missing:
            raise ValueError(f"Missing required metadata fields: {missing}")
    
    @staticmethod
    def enrich_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add auto-generated metadata fields.
        
        Args:
            metadata: Base metadata
            
        Returns:
            Enriched metadata
        """
        enriched = metadata.copy()
        
        # Add timestamp
        if 'date_added' not in enriched:
            enriched['date_added'] = datetime.now().isoformat()
        
        # Add language default
        if 'language' not in enriched:
            enriched['language'] = 'en'
        
        # Ensure tags is a list
        if 'tags' in enriched and not isinstance(enriched['tags'], list):
            enriched['tags'] = [enriched['tags']]
        
        return enriched
    
    @staticmethod
    def merge_metadata(
        base_metadata: Dict[str, Any],
        chunk_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge base document metadata with chunk-specific metadata.
        
        Args:
            base_metadata: Document-level metadata
            chunk_metadata: Chunk-specific metadata (chunk_index, etc.)
            
        Returns:
            Merged metadata
        """
        merged = base_metadata.copy()
        merged.update(chunk_metadata)
        return merged


def create_metadata(
    machine_id: str,
    source_file: str,
    doc_type: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create metadata dict for a document.
    
    Args:
        machine_id: Machine identifier
        source_file: Source filename
        doc_type: Document type (manual, procedure, etc.)
        **kwargs: Additional metadata fields
        
    Returns:
        Metadata dict
    """
    metadata = {
        'machine_id': machine_id,
        'source_file': source_file,
    }
    
    if doc_type:
        metadata['doc_type'] = doc_type
    
    # Add any additional fields
    metadata.update(kwargs)
    
    # Validate and enrich
    MetadataManager.validate_metadata(metadata)
    return MetadataManager.enrich_metadata(metadata)
