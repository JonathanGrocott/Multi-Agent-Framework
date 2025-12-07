"""File loaders for different document formats."""

import json
from pathlib import Path
from typing import Dict, Any, List


class DocumentLoader:
    """Base class for document loaders."""
    
    def load(self, file_path: str) -> Dict[str, Any]:
        """
        Load a document and return its content and metadata.
        
        Returns:
            dict with 'content' (str) and 'metadata' (dict)
        """
        raise NotImplementedError


class TextLoader(DocumentLoader):
    """Loader for plain text files (.txt)."""
    
    def load(self, file_path: str) -> Dict[str, Any]:
        """Load a text file."""
        path = Path(file_path)
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            'content': content,
            'metadata': {
                'source_file': path.name,
                'file_type': 'text',
                'file_size': path.stat().st_size
            }
        }


class MarkdownLoader(DocumentLoader):
    """Loader for markdown files (.md)."""
    
    def load(self, file_path: str) -> Dict[str, Any]:
        """Load a markdown file."""
        path = Path(file_path)
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title from first # heading if present
        title = None
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        
        return {
            'content': content,
            'metadata': {
                'source_file': path.name,
                'file_type': 'markdown',
                'file_size': path.stat().st_size,
                'title': title
            }
        }


class JSONLoader(DocumentLoader):
    """Loader for JSON files (.json)."""
    
    def load(self, file_path: str) -> Dict[str, Any]:
        """
        Load a JSON file and convert to text.
        
        Flattens the JSON structure into readable text.
        """
        path = Path(file_path)
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert JSON to readable text
        content = self._json_to_text(data)
        
        return {
            'content': content,
            'metadata': {
                'source_file': path.name,
                'file_type': 'json',
                'file_size': path.stat().st_size
            }
        }
    
    def _json_to_text(self, obj: Any, prefix: str = '') -> str:
        """Recursively convert JSON to text."""
        lines = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    lines.append(self._json_to_text(value, prefix + '  '))
                else:
                    lines.append(f"{prefix}{key}: {value}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}[{i}]:")
                    lines.append(self._json_to_text(item, prefix + '  '))
                else:
                    lines.append(f"{prefix}- {item}")
        else:
            lines.append(f"{prefix}{obj}")
        
        return '\n'.join(lines)


def get_loader(file_path: str) -> DocumentLoader:
    """
    Get appropriate loader based on file extension.
    
    Args:
        file_path: Path to file
        
    Returns:
        DocumentLoader instance
        
    Raises:
        ValueError: If file type not supported
    """
    ext = Path(file_path).suffix.lower()
    
    loaders = {
        '.txt': TextLoader,
        '.md': MarkdownLoader,
        '.markdown': MarkdownLoader,
        '.json': JSONLoader,
    }
    
    if ext not in loaders:
        raise ValueError(
            f"Unsupported file type: {ext}. "
            f"Supported types: {', '.join(loaders.keys())}"
        )
    
    return loaders[ext]()


def load_document(file_path: str) -> Dict[str, Any]:
    """
    Load a document using the appropriate loader.
    
    Args:
        file_path: Path to document file
        
    Returns:
        Document dict with 'content' and 'metadata'
    """
    loader = get_loader(file_path)
    return loader.load(file_path)
