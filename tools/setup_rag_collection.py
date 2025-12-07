"""Quick setup script for RAG collections."""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from rag_ingestion.ingest import DocumentIngestion


def setup_collection(
    machine_id: str,
    docs_directory: str,
    collection_name: str = None,
    chromadb_path: str = "./chromadb_data",
    doc_type: str = None
):
    """
    Quick setup for a machine's RAG collection.
    
    Args:
        machine_id: Machine identifier
        docs_directory: Directory containing documents
        collection_name: Collection name (defaults to {machine_id}_docs)
        chromadb_path: Path to ChromaDB storage
        doc_type: Document type
    """
    if not collection_name:
        collection_name = f"{machine_id}_docs"
    
    print(f"Setting up RAG collection for {machine_id}")
    print(f"Collection: {collection_name}")
    print(f"Docs directory: {docs_directory}")
    print(f"ChromaDB path: {chromadb_path}")
    print()
    
    # Initialize ingestion
    ingestion = DocumentIngestion(chromadb_path=chromadb_path)
    
    # Prepare metadata
    metadata = {}
    if doc_type:
        metadata['doc_type'] = doc_type
    
    # Ingest directory
    try:
        total_chunks = ingestion.ingest_directory(
            directory=docs_directory,
            collection_name=collection_name,
            machine_id=machine_id,
            metadata=metadata,
            recursive=True
        )
        
        print()
        print("=" * 60)
        print(f"✓ Setup complete!")
        print(f"  Machine: {machine_id}")
        print(f"  Collection: {collection_name}")
        print(f"  Total chunks: {total_chunks}")
        print()
        print("Add this to your machine config YAML:")
        print()
        print(f"  mcp_servers:")
        print(f"    chromadb:")
        print(f"      type: 'chromadb'")
        print(f"      collection_name: '{collection_name}'")
        print(f"      persist_directory: '{chromadb_path}'")
        print()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Quick setup for RAG collection'
    )
    
    parser.add_argument(
        '--machine',
        required=True,
        help='Machine ID'
    )
    parser.add_argument(
        '--docs',
        required=True,
        help='Directory containing documents'
    )
    parser.add_argument(
        '--collection',
        help='Collection name (default: {machine}_docs)'
    )
    parser.add_argument(
        '--chromadb-path',
        default='./chromadb_data',
        help='Path to ChromaDB storage'
    )
    parser.add_argument(
        '--doc-type',
        help='Document type (manual, procedure, etc.)'
    )
    
    args = parser.parse_args()
    
    setup_collection(
        machine_id=args.machine,
        docs_directory=args.docs,
        collection_name=args.collection,
        chromadb_path=args.chromadb_path,
        doc_type=args.doc_type
    )


if __name__ == '__main__':
    main()
