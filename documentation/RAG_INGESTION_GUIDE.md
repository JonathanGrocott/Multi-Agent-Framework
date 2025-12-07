# RAG Document Ingestion Guide

## Overview

This guide explains how to add documents to machine-specific RAG collections in ChromaDB for intelligent document retrieval.

## Quick Start

### Option 1: One-Command Setup (Easiest)

```bash
# Set up a complete RAG collection for a machine
python tools/setup_rag_collection.py \
  --machine machine1 \
  --docs ./docs/machine1/
```

That's it! Your documents are now indexed and ready to use.

### Option 2: Manual Ingestion (More Control)

```bash
# Ingest a single file
python tools/rag_ingestion/ingest.py \
  --machine machine1 \
  --collection machine1_docs \
  --file ./docs/machine1/manual.md \
  --doc-type manual

# Ingest an entire directory
python tools/rag_ingestion/ingest.py \
  --machine machine2 \
  --collection machine2_docs \
  --directory ./docs/machine2/ \
  --recursive \
  --metadata '{"doc_type": "procedures", "version": "2024"}'
```

## Supported File Formats

| Format | Extensions | Notes |
|--------|-----------|-------|
| **Text** | `.txt` | Plain text files |
| **Markdown** | `.md`, `.markdown` | Preserves heading structure |
| **JSON** | `.json` | Automatically flattened to text |

## Document Chunking

Documents are automatically chunked using **semantic chunking**:

- ✅ Split by paragraphs and sections
- ✅ Max 1000 tokens per chunk
- ✅ Overlap between chunks for context
- ✅ Preserves document structure

### Example

**Input Document**:
```markdown
# Machine Manual

## Setup
Follow these steps...

## Troubleshooting
If error occurs...
```

**Output**: 2-3 semantic chunks with metadata, each containing 1-2 sections.

## Metadata System

### Required Metadata (Auto-generated)

- `machine_id` - Machine identifier
- `source_file` - Original filename
- `chunk_index` - Chunk number
- `date_added` - Timestamp

### Optional Metadata (User-provided)

- `doc_type` - "manual", "procedure", "specification"
- `version` - Document version
- `author` - Document author
- `section` - Document section
- `tags` - List of tags
- `language` - Language code (default: "en")

### Adding Custom Metadata

```bash
python tools/rag_ingestion/ingest.py \
  --machine spar_lam \
  --collection spar_lam_docs \
  --file manual.md \
  --metadata '{
    "doc_type": "manual",
    "version": "2.1",
    "author": "Engineering Team",
    "tags": ["setup", "maintenance"]
  }'
```

## Collection Organization

Each machine gets its own isolated collection:

```
chromadb_data/
├── machine1_docs/          # Machine 1 documents
├── machine2_docs/          # Machine 2 documents  
└── company_shared_docs/    # Shared documents
```

Agents can ONLY access collections listed in their config - complete isolation!

## Using in Agent Config

After ingesting documents, add to your machine config:

```yaml
# backend/configs/machine1.yaml

agents:
  - agent_id: "machine1_rag"
    name: "Machine 1 Documentation Search"
    machine_id: "machine1"
    function: "data_fetching"
    capabilities:
      - "search_documentation"
    mcp_tools:
      - server: "chromadb"
        tools:
          - "search_machine1_docs"

mcp_servers:
  chromadb:
    type: "chromadb"
    collection_name: "machine1_docs"
    persist_directory: "./chromadb_data"
```

## CLI Reference

### Main Ingestion Tool

```bash
python tools/rag_ingestion/ingest.py [OPTIONS]
```

**Options**:
- `--machine MACHINE_ID` - Machine identifier (required)
- `--collection NAME` - Collection name (required)
- `--file PATH` - Single file to ingest
- `--directory PATH` - Directory to ingest
- `--recursive` - Search subdirectories
- `--metadata JSON` - Additional metadata as JSON
- `--doc-type TYPE` - Document type
- `--chromadb-path PATH` - ChromaDB location (default: ./chromadb_data)
- `--list-collections` - List all collections
- `--stats COLLECTION` - Get collection statistics

### Quick Setup Tool

```bash
python tools/setup_rag_collection.py [OPTIONS]
```

**Options**:
- `--machine MACHINE_ID` - Machine identifier (required)
- `--docs PATH` - Documents directory (required)
- `--collection NAME` - Collection name (optional, defaults to {machine}_docs)
- `--doc-type TYPE` - Document type
- `--chromadb-path PATH` - ChromaDB location

## Examples

### Example 1: Machine Manual

```bash
# Create docs directory
mkdir -p docs/spar_lamination

# Add manual (markdown file)
cat > docs/spar_lamination/operating_manual.md << 'EOF'
# Spar Lamination Machine

## Overview
This machine is used for...

## Setup Instructions
1. Connect power
2. Calibrate sensors
EOF

# Ingest
python tools/setup_rag_collection.py \
  --machine spar_lamination \
  --docs ./docs/spar_lamination/ \
  --doc-type manual
```

### Example 2: Multiple Document Types

```bash
# Procedures directory
mkdir -p docs/robot_a/procedures
mkdir -p docs/robot_a/specs

# Add files
echo "Startup procedure..." > docs/robot_a/procedures/startup.txt
echo "# Technical Specifications" > docs/robot_a/specs/tech_spec.md

# Ingest with metadata
python tools/rag_ingestion/ingest.py \
  --machine robot_a \
  --collection robot_a_docs \
  --directory ./docs/robot_a/ \
  --recursive \
  --metadata '{"maintenance_level": "L2"}'
```

### Example 3: JSON Configuration Files

```bash
# Create JSON config
cat > docs/machine2/config.json << 'EOF'
{
  "name": "Machine 2",
  "settings": {
    "temperature": 185,
    "pressure": 4.5
  },
  "procedures": [
    {"name": "Startup", "steps": ["Step 1", "Step 2"]},
    {"name": "Shutdown", "steps": ["Step A", "Step B"]}
  ]
}
EOF

# Ingest
python tools/rag_ingestion/ingest.py \
  --machine machine2 \
  --collection machine2_docs \
  --file ./docs/machine2/config.json \
  --doc-type configuration
```

## Management Commands

### List Collections

```bash
python tools/rag_ingestion/ingest.py --list-collections
```

Output:
```
Collections:
  - machine1_docs: 45 documents
    Metadata: {'machine_id': 'machine1'}
  - machine2_docs: 23 documents
    Metadata: {'machine_id': 'machine2'}
```

### Collection Statistics

```bash
python tools/rag_ingestion/ingest.py --stats machine1_docs
```

### Search Test

After ingesting, test the collection:

```python
import chromadb

client = chromadb.PersistentClient(path="./chromadb_data")
collection = client.get_collection("machine1_docs")

# Search
results = collection.query(
    query_texts=["troubleshooting error code"],
    n_results=3
)

print(results['documents'][0])
```

## Best Practices

### 1. Organize Documents by Machine

```
docs/
├── spar_lamination/
│   ├── manual.md
│   ├── procedures/
│   └── specs/
├── robot_a/
│   └── ...
└── shared/
    └── safety_guidelines.md
```

### 2. Use Consistent Metadata

```bash
# Always include doc_type
--doc-type manual
--doc-type procedure
--doc-type specification
--doc-type troubleshooting
```

### 3. Version Your Documents

```bash
--metadata '{"version": "2.1", "date": "2024-12-06"}'
```

### 4. Tag for Better Search

```bash
--metadata '{"tags": ["safety", "electrical", "maintenance"]}'
```

## Troubleshooting

### "Unsupported file type" Error

Only `.txt`, `.md`, `.markdown`, and `.json` are supported. Convert other formats first.

### "Missing required metadata" Error

Ensure `--machine` and `--collection` are provided for ingestion commands.

### Empty Collection

Check that files exist in the directory and have supported extensions.

### Can't Find Documents

Verify collection name matches the one in your agent config YAML.

## Integration with Agents

After ingesting documents, agents can search them automatically:

**User asks**: "How do I troubleshoot error E01?"

**Agent workflow**:
1. RAG agent searches `machine1_docs` collection
2. Finds relevant chunks about error E01
3. LLM uses retrieved docs to answer question
4. Returns: "Error E01 is a temperature sensor malfunction. Solution: Power down, check sensor cables..."

## Summary

**Quick workflow**:
1. Organize docs in `docs/{machine_id}/` directory
2. Run: `python tools/setup_rag_collection.py --machine {id} --docs ./docs/{id}/`
3. Add ChromaDB config to machine YAML
4. Agents can now search documentation!

Your documentation is now part of the multi-agent system's knowledge base!
