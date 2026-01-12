# RAG Application Backend

FastAPI backend with entity extraction and multi-strategy search capabilities.

## Features

- **PDF Processing**: Extract text, chunk documents, and process PDFs
- **Entity Extraction**: GPT-4o-mini structured outputs for extracting people, organizations, locations, topics, and technical terms
- **Multi-Strategy Search**:
  - BM25 (keyword search)
  - Semantic (vector similarity)
  - Entity (entity-based filtering)
  - Hybrid (BM25 + Semantic with RRF)
  - Advanced (all methods combined)
- **RAG Query**: Retrieve and generate answers using GPT-4o-mini
- **Redis Caching**: Semantic cache for 70% cost reduction
- **Azure Integration**: Blob Storage, AI Search, OpenAI

## Tech Stack

- FastAPI 0.115+
- Python 3.12+
- Azure OpenAI (GPT-4o-mini, text-embedding-3-small)
- Azure AI Search
- Azure Blob Storage
- Redis
- uv (package manager)

## Setup

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Azure credentials
   ```

3. **Run locally**:
   ```bash
   uv run uvicorn backend.main:app --reload
   ```

4. **Run with Docker**:
   ```bash
   docker build -t rag-backend .
   docker run -p 8000:8000 --env-file .env rag-backend
   ```

## API Endpoints

### Upload
- `POST /api/upload` - Upload PDF file

### Indexing
- `POST /api/index/{document_id}` - Start document indexing
- `GET /api/index/{document_id}` - Get indexing status

### Query
- `POST /api/query/search` - Multi-strategy search
- `POST /api/query/rag` - RAG query with answer generation

### Health
- `GET /health` - Health check
- `GET /` - Root endpoint

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

```bash
# Run with auto-reload
uv run uvicorn backend.main:app --reload --log-level debug

# Run tests
uv run pytest

# Format code
uv run black src/
uv run ruff check src/
```

## Environment Variables

See `.env.example` for all configuration options.

## License

MIT
