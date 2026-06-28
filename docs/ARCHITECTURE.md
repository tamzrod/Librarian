# ARCHITECTURE.md

## Core Abstractions

Librarian operates on five fundamental abstractions:

| Abstraction | Description | Example |
|-------------|-------------|---------|
| **Document** | A unit of indexed content with text and metadata | A file, email, or record |
| **Entity** | A named thing discovered in documents | Person, company, location, concept |
| **Relationship** | A connection between entities | "works for", "located in", "mentions" |
| **Event** | A timestamped occurrence | Meeting, purchase, update |
| **Timeline** | A sequence of events ordered by time | Project history, travel log |
| **Collection** | A group of related documents | Project folder, email thread |

## Ingestion Pipeline

```
Filesystem
    ↓
Scanner
    ↓
Parser Registry
    ↓
Parser (domain-specific plugin)
    ↓
Chunker
    ↓
Indexer
    ↓
Persistence
    ↓
Retriever
    ↓
Reasoning Layer
```

### Pipeline Stages

1. **Scanner**: Discovers files in the filesystem
2. **Parser Registry**: Routes files to appropriate parser based on extension
3. **Parser**: Extracts structured data from file content (domain-specific)
4. **Chunker**: Splits content into manageable segments
5. **Indexer**: Creates searchable index with metadata
6. **Persistence**: Saves index for future retrieval
7. **Retriever**: Searches index for relevant documents
8. **Reasoning Layer**: Assembles context for LLM consumption

## Domain-Specific Parsers

Parsers are plugins designed for specific knowledge domains:

### Software
```python
{
    "imports": ["module_a", "module_b"],
    "classes": ["MyClass"],
    "functions": ["my_function"]
}
```

### Business
```python
{
    "customers": ["ABC Corp"],
    "invoices": ["INV-001"],
    "meetings": ["Q4 Planning"]
}
```

### Personal Memory
```python
{
    "GPS history": ["Home", "Office"],
    "calendar events": ["Doctor appointment"],
    "photos": ["beach_sunset.jpg"],
    "receipts": ["grocery_store"],
    "emails": ["contract signed"]
}
```

### Stories
```python
{
    "characters": ["Alice", "Bob"],
    "locations": ["Wonderland", "Rabbit Hole"],
    "events": ["Tea party"]
}
```

### Research
```python
{
    "citations": ["Smith et al. 2023"],
    "authors": ["Dr. Jane Smith"],
    "topics": ["machine learning", "neural networks"]
}
```

## Component Responsibilities

- **Scanner**: Detects files, computes hashes, tracks modifications
- **Parser Registry**: Routes files to appropriate domain-specific parser
- **Parsers**: Extract structured domain knowledge from unstructured content
- **Chunker**: Splits content for manageable processing
- **Indexer**: Creates searchable index preserving entities and relationships
- **Persistence**: Saves/loads index to/from storage
- **Retriever**: Searches index using keywords, entities, or relationships
- **Reasoning Layer**: Assembles context packages for LLM reasoning

