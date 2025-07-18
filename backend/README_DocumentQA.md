# Document Q&A System with RAG

A comprehensive Document Q&A system built with FastAPI that uses RAG (Retrieval-Augmented Generation) combining FAISS vector search, sentence-transformers embeddings, and Groq's LLaMA3-70B model for intelligent question answering.

## Features

- **Document Upload**: Support for PDF, DOCX, TXT, and MD files
- **Smart Text Processing**: Automatic text extraction and chunking with overlap
- **Vector Search**: FAISS-based semantic search with sentence-transformers embeddings
- **RAG Pipeline**: Retrieval-Augmented Generation using Groq LLaMA3-70B
- **Real-time Q&A**: Ask questions and get contextual answers with source references
- **Document Management**: Full CRUD operations for documents
- **Multi-user Support**: User authentication and document sharing
- **Background Processing**: Async document processing
- **Comprehensive API**: RESTful endpoints for all operations

## Tech Stack

- **Backend**: FastAPI with async/await support
- **Vector DB**: FAISS for efficient similarity search
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **LLM**: Groq LLaMA3-70B (llama3-70b-8192)
- **Database**: SQLAlchemy ORM with PostgreSQL/SQLite support
- **Text Processing**: PyMuPDF, python-docx, markdown
- **Authentication**: Supabase integration
- **File Storage**: Local filesystem with configurable paths

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements/base.txt
```

2. Set up environment variables in `.env`:
```env
# Groq Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama3-70b-8192

# Document Processing
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=400
CHUNK_OVERLAP=50
MAX_CONCURRENT_PROCESSING=3

# Vector Store
VECTOR_STORE_PATH=./vector_store

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_PATH=./uploads
ALLOWED_EXTENSIONS=.pdf,.docx,.txt,.md

# Database
DATABASE_URL=postgresql://user:password@localhost/db
```

3. Create necessary directories:
```bash
mkdir -p uploads vector_store
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Document Management

#### Upload Document
```bash
POST /api/v1/documents/upload
Content-Type: multipart/form-data

curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "title=Research Paper" \
  -F "description=AI research paper on neural networks" \
  -F "tags=AI,research,neural networks"
```

Response:
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Document uploaded successfully. Processing will begin shortly.",
  "processing_status": "pending"
}
```

#### List Documents
```bash
GET /api/v1/documents/?skip=0&limit=20&status=completed

curl -X GET "http://localhost:8000/api/v1/documents/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
  "documents": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Research Paper",
      "description": "AI research paper on neural networks",
      "filename": "document.pdf",
      "file_type": "application/pdf",
      "file_size": 2048576,
      "processing_status": "completed",
      "chunk_count": 25,
      "total_tokens": 5000,
      "tags": ["AI", "research", "neural networks"],
      "created_at": "2023-01-01T12:00:00Z",
      "updated_at": "2023-01-01T12:05:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

#### Get Document Details
```bash
GET /api/v1/documents/{document_id}

curl -X GET "http://localhost:8000/api/v1/documents/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Question & Answer

#### Ask Question
```bash
POST /api/v1/documents/{document_id}/ask
Content-Type: application/json

curl -X POST "http://localhost:8000/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/ask" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main findings in this research paper?",
    "max_chunks": 5,
    "include_sources": true,
    "context_window": 4000
  }'
```

Response:
```json
{
  "answer": "Based on the document, the main findings include: 1) Neural networks show significant improvement in accuracy when using attention mechanisms, 2) The proposed architecture achieves 95% accuracy on the test dataset, 3) Training time is reduced by 40% compared to previous methods.",
  "confidence_score": 0.92,
  "sources": [
    {
      "chunk_id": "456e7890-e89b-12d3-a456-426614174001",
      "page_number": 1,
      "content_preview": "Our experiments demonstrate that the proposed neural network architecture achieves...",
      "relevance_score": 0.95
    }
  ],
  "processing_time": 1.25,
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "chunks_used": 3
}
```

#### Document Summary
```bash
POST /api/v1/documents/{document_id}/summarize
Content-Type: application/json

curl -X POST "http://localhost:8000/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/summarize" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "summary_type": "comprehensive",
    "max_length": 500,
    "focus_areas": ["methodology", "results"]
  }'
```

Response:
```json
{
  "summary": "This paper presents a novel neural network architecture for image classification. The methodology involves using attention mechanisms combined with residual connections. The results show 95% accuracy on standard benchmarks, outperforming previous state-of-the-art methods by 3.2%.",
  "summary_type": "comprehensive",
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "key_concepts": [],
  "generated_at": "2023-01-01T12:10:00Z"
}
```

#### Search Document
```bash
POST /api/v1/documents/{document_id}/search
Content-Type: application/json

curl -X POST "http://localhost:8000/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/search" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "attention mechanism",
    "max_results": 10,
    "threshold": 0.7
  }'
```

Response:
```json
{
  "query": "attention mechanism",
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "passages": [
    {
      "content": "The attention mechanism allows the model to focus on relevant parts of the input sequence...",
      "page_number": 3,
      "chunk_index": 8,
      "relevance_score": 0.89,
      "preview": "The attention mechanism allows the model to focus on relevant parts..."
    }
  ],
  "total_found": 1
}
```

### Document Operations

#### Delete Document
```bash
DELETE /api/v1/documents/{document_id}

curl -X DELETE "http://localhost:8000/api/v1/documents/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Reprocess Document
```bash
POST /api/v1/documents/{document_id}/reprocess

curl -X POST "http://localhost:8000/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/reprocess" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get Document Statistics
```bash
GET /api/v1/documents/{document_id}/stats

curl -X GET "http://localhost:8000/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
  "total_vectors": 25,
  "embedding_dimension": 384,
  "index_type": "IndexFlatIP",
  "index_size_bytes": 38400,
  "metadata_size_bytes": 15360
}
```

### Q&A History and Feedback

#### Get Q&A History
```bash
GET /api/v1/documents/{document_id}/qa-history?limit=50

curl -X GET "http://localhost:8000/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/qa-history" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Rate Q&A Interaction
```bash
POST /api/v1/documents/qa-interactions/{interaction_id}/rate

curl -X POST "http://localhost:8000/api/v1/documents/qa-interactions/789e0123-e89b-12d3-a456-426614174002/rate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 5,
    "feedback": "Very helpful and accurate answer"
  }'
```

### System Health

#### Health Check
```bash
GET /api/v1/documents/system/health

curl -X GET "http://localhost:8000/api/v1/documents/system/health"
```

Response:
```json
{
  "status": "healthy",
  "embedding_service": {
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "embedding_dimension": 384,
    "max_sequence_length": 512,
    "model_type": "SentenceTransformer",
    "device": "cpu"
  },
  "vector_store": {
    "total_indices": 5,
    "total_size_bytes": 204800,
    "total_size_mb": 0.2,
    "vector_store_path": "./vector_store"
  },
  "timestamp": "2023-01-01T12:00:00Z"
}
```

## RAG Pipeline Architecture

### 1. Document Processing Pipeline

```
Document Upload → Text Extraction → Chunking → Embedding Generation → FAISS Index Creation
```

- **Text Extraction**: PyMuPDF for PDFs, python-docx for Word documents
- **Chunking**: Overlapping text chunks (400 tokens, 50 token overlap)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- **Storage**: FAISS IndexFlatIP for cosine similarity search

### 2. Question Answering Pipeline

```
Question → Query Embedding → Vector Search → Context Retrieval → LLM Generation → Response
```

- **Query Embedding**: Same model as document embeddings
- **Vector Search**: FAISS similarity search with configurable threshold
- **Context Building**: Top-K relevant chunks with metadata
- **LLM Generation**: Groq LLaMA3-70B with structured prompts
- **Response**: Answer with confidence score and source references

### 3. System Prompt Template

```
You are an expert document analyst. Your task is to answer questions based strictly on the provided context from the document "{document_title}".

IMPORTANT GUIDELINES:
1. ONLY use information from the provided context
2. If the context doesn't contain relevant information, say so clearly
3. Be precise and concise in your answers
4. Include specific references when possible (e.g., "According to Context 1...")
5. If you're uncertain, express that uncertainty
6. Do not make up information not found in the context

CONTEXT FROM DOCUMENT:
{context_text}

Please answer the following question based ONLY on the context provided above.
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API key for LLaMA3-70B | Required |
| `GROQ_MODEL` | Groq model name | `llama3-70b-8192` |
| `EMBEDDING_MODEL_NAME` | HuggingFace model for embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| `CHUNK_SIZE` | Text chunk size in tokens | `400` |
| `CHUNK_OVERLAP` | Overlap between chunks in tokens | `50` |
| `MAX_CONCURRENT_PROCESSING` | Max parallel document processing | `3` |
| `VECTOR_STORE_PATH` | Path for FAISS indices | `./vector_store` |
| `MAX_FILE_SIZE` | Maximum file size in bytes | `10485760` (10MB) |
| `UPLOAD_PATH` | Path for uploaded files | `./uploads` |
| `ALLOWED_EXTENSIONS` | Supported file extensions | `.pdf,.docx,.txt,.md` |

### File Format Support

| Format | Extension | Library | Notes |
|--------|-----------|---------|-------|
| PDF | `.pdf` | PyMuPDF | Supports text extraction, page numbers |
| Word | `.docx` | python-docx | Supports tables and formatting |
| Text | `.txt` | Built-in | Plain text files |
| Markdown | `.md` | markdown | Converted to plain text |

## Performance Optimization

### Embedding Generation
- Uses sentence-transformers for fast, high-quality embeddings
- Batch processing for multiple documents
- Async processing to avoid blocking

### Vector Search
- FAISS IndexFlatIP for exact cosine similarity
- Configurable similarity thresholds
- Efficient metadata storage

### LLM Integration
- Groq for fast inference (LLaMA3-70B)
- Structured prompts for consistent responses
- Configurable temperature and context windows

## Error Handling

The system includes comprehensive error handling:

- **Document Processing Errors**: File format, size, extraction issues
- **Vector Store Errors**: Index creation, search failures
- **LLM Errors**: API timeouts, rate limiting, model failures
- **Database Errors**: Connection issues, constraint violations
- **Authentication Errors**: Invalid tokens, unauthorized access

## Security Features

- **User Authentication**: Supabase integration with JWT tokens
- **File Validation**: Type checking and size limits
- **Input Sanitization**: Query and document validation
- **Access Control**: User-based document permissions
- **Rate Limiting**: Configurable request limits

## Monitoring and Logging

- **Structured Logging**: JSON format with context
- **Performance Metrics**: Response times, token usage
- **Health Checks**: System status endpoints
- **Error Tracking**: Comprehensive exception handling

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
black app/
isort app/
flake8 app/
```

### Database Migrations
```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Production Deployment

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements/ requirements/
RUN pip install -r requirements/prod.txt

COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Setup
- Set production environment variables
- Configure database connections
- Set up file storage (S3, GCS, etc.)
- Configure monitoring and logging
- Set up load balancing and scaling

## Troubleshooting

### Common Issues

1. **Document processing fails**
   - Check file format and size
   - Verify text extraction libraries
   - Review error logs

2. **Vector search returns no results**
   - Check embedding model consistency
   - Verify FAISS index creation
   - Adjust similarity threshold

3. **LLM responses are poor**
   - Review prompt engineering
   - Check context window size
   - Verify model parameters

4. **Performance issues**
   - Monitor embedding generation time
   - Check vector search performance
   - Review database query optimization

### Debug Commands

```bash
# Check system health
curl http://localhost:8000/api/v1/documents/system/health

# View logs
tail -f logs/app.log

# Check database connections
python -c "from app.config.database import SessionLocal; print('DB OK')"

# Test embedding service
python -c "from app.services.embedding_service import EmbeddingService; es = EmbeddingService(); print('Embeddings OK')"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.