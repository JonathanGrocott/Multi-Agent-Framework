"""Main document ingestion script for RAG."""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any
import json
import chromadb
from chromadb.config import Settings

from rag_ingestion import load_document, chunk_document, create_metadata


class DocumentIngestion:
    """Main class for ingesting documents into ChromaDB."""
    
    def __init__(self, chromadb_path: str = "./chromadb_data"):
        """
        Initialize ingestion system.
        
        Args:
            chromadb_path: Path to ChromaDB storage
        """
        self.client = chromadb.PersistentClient(path=chromadb_path)
        self.chromadb_path = chromadb_path
    
    def ingest_file(
        self,
        file_path: str,
        collection_name: str,
        machine_id: str,
        metadata: Dict[str, Any] = None
    ) -> int:
        """
        Ingest a single file into a collection.
        
        Args:
            file_path: Path to file
            collection_name: ChromaDB collection name
            machine_id: Machine identifier
            metadata: Additional metadata
            
        Returns:
            Number of chunks added
        """
        print(f"Loading {file_path}...")
        
        # Load document
        doc = load_document(file_path)
        
        # Create metadata
        doc_metadata = create_metadata(
            machine_id=machine_id,
            source_file=Path(file_path).name,
            **(metadata or {})
        )
        
        # Merge with file metadata
        doc_metadata.update(doc['metadata'])
        
        # Chunk document
        print(f"Chunking document...")
        chunks = chunk_document(doc['content'], doc_metadata)
        
        print(f"Created {len(chunks)} chunks")
        
        # Get or create collection
        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"machine_id": machine_id}
        )
        
        # Add chunks to collection
        documents = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            doc_id = f"{Path(file_path).stem}_{chunk['metadata']['chunk_index']}"
            documents.append(chunk['content'])
            metadatas.append(chunk['metadata'])
            ids.append(doc_id)
        
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✓ Added {len(chunks)} chunks to collection '{collection_name}'")
        return len(chunks)
    
    def ingest_directory(
        self,
        directory: str,
        collection_name: str,
        machine_id: str,
        metadata: Dict[str, Any] = None,
        recursive: bool = False
    ) -> int:
        """
        Ingest all supported files from a directory.
        
        Args:
            directory: Directory path
            collection_name: ChromaDB collection name
            machine_id: Machine identifier
            metadata: Additional metadata for all files
            recursive: Whether to search subdirectories
            
        Returns:
            Total number of chunks added
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise ValueError(f"Directory not found: {directory}")
        
        # Find all supported files
        pattern = '**/*' if recursive else '*'
        supported_extensions = {'.txt', '.md', '.markdown', '.json'}
        
        files = [
            f for f in dir_path.glob(pattern)
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]
        
        if not files:
            print(f"No supported files found in {directory}")
            return 0
        
        print(f"Found {len(files)} files to ingest")
        
        total_chunks = 0
        for file_path in files:
            try:
                chunks = self.ingest_file(
                    str(file_path),
                    collection_name,
                    machine_id,
                    metadata
                )
                total_chunks += chunks
            except Exception as e:
                print(f"✗ Error processing {file_path}: {e}")
        
        return total_chunks
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """List all collections with stats."""
        collections = self.client.list_collections()
        
        result = []
        for col in collections:
            result.append({
                'name': col.name,
                'count': col.count(),
                'metadata': col.metadata
            })
        
        return result
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a collection."""
        try:
            collection = self.client.get_collection(collection_name)
            return {
                'name': collection_name,
                'document_count': collection.count(),
                'metadata': collection.metadata
            }
        except Exception as e:
            return {'error': str(e)}


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Ingest documents into ChromaDB for RAG'
    )
    
    # Required args
    parser.add_argument(
        '--machine',
        required=False,
        help='Machine ID (required for ingestion)'
    )
    parser.add_argument(
        '--collection',
        required=False,
        help='ChromaDB collection name (required for ingestion)'
    )
    
    # Input source
    parser.add_argument(
        '--file',
        help='Single file to ingest'
    )
    parser.add_argument(
        '--directory',
        help='Directory of files to ingest'
    )
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Recursively search directory'
    )
    
    # Metadata
    parser.add_argument(
        '--metadata',
        help='Additional metadata as JSON string'
    )
    parser.add_argument(
        '--doc-type',
        help='Document type (manual, procedure, etc.)'
    )
    
    # ChromaDB
    parser.add_argument(
        '--chromadb-path',
        default='./chromadb_data',
        help='Path to ChromaDB storage (default: ./chromadb_data)'
    )
    
    # Actions
    parser.add_argument(
        '--list-collections',
        action='store_true',
        help='List all collections and exit'
    )
    parser.add_argument(
        '--stats',
        help='Get stats for a collection'
    )
    
    args = parser.parse_args()
    
    # Initialize ingestion
    ingestion = DocumentIngestion(chromadb_path=args.chromadb_path)
    
    # Handle list collections
    if args.list_collections:
        collections = ingestion.list_collections()
        print("\nCollections:")
        for col in collections:
            print(f"  - {col['name']}: {col['count']} documents")
            if col['metadata']:
                print(f"    Metadata: {col['metadata']}")
        return
    
    # Handle stats
    if args.stats:
        stats = ingestion.get_collection_stats(args.stats)
        print(f"\nCollection: {args.stats}")
        print(f"Documents: {stats.get('document_count', 'N/A')}")
        print(f"Metadata: {stats.get('metadata', {})}")
        return
    
    # Validate required args for ingestion
    if not args.machine or not args.collection:
        parser.error("--machine and --collection are required for ingestion")
    
    if not args.file and not args.directory:
        parser.error("Either --file or --directory must be specified")
    
    # Parse additional metadata
    metadata = {}
    if args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError as e:
            print(f"Error parsing metadata JSON: {e}")
            sys.exit(1)
    
    if args.doc_type:
        metadata['doc_type'] = args.doc_type
    
    # Perform ingestion
    try:
        if args.file:
            chunks = ingestion.ingest_file(
                args.file,
                args.collection,
                args.machine,
                metadata
            )
            print(f"\n✓ Successfully ingested {chunks} chunks")
        
        elif args.directory:
            chunks = ingestion.ingest_directory(
                args.directory,
                args.collection,
                args.machine,
                metadata,
                recursive=args.recursive
            )
            print(f"\n✓ Successfully ingested {chunks} total chunks")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
