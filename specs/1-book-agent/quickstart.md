# Quickstart Guide: AI-Enhanced Interactive Book Agent

## Prerequisites
- Python 3.12+
- Docker and Docker Compose (for local development)
- Google Cloud account with access to Gemini API
- PostgreSQL database (local or cloud)

## Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/book-agent.git
cd book-agent
```

### 2. Set up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://username:password@localhost/book_agent_db
GOOGLE_API_KEY=your_gemini_api_key
JWT_SECRET_KEY=your_jwt_secret_key
CHROMADB_PATH=./chroma_data
MAX_BOOK_PAGES=700
MAX_CONCURRENT_USERS=600
```

### 5. Database Setup
```bash
# Run database migrations
python -m alembic upgrade head
```

### 6. Initialize the Application
```bash
# Start the backend server
cd backend
python -m uvicorn main:app --reload --port 8000

# In another terminal, start the frontend (if applicable)
cd frontend
npm install
npm run dev
```

## Running Tests
```bash
# Run all tests
python -m pytest

# Run tests with coverage
python -m pytest --cov=src

# Run specific test file
python -m pytest tests/test_api.py
```

## Key Endpoints

### Authentication
- `POST /auth/register` - Create new user account
- `POST /auth/login` - User login

### Book Management
- `POST /books` - Upload and process a book
- `GET /books/{book_id}` - Get book details

### AI Features
- `POST /books/{book_id}/search` - Semantic search within book
- `POST /books/{book_id}/explain` - Explain book content
- `POST /books/{book_id}/summarize` - Summarize book content

### Session Management
- `GET /sessions/current` - Get current reading session
- `GET /sessions/{session_id}` - Get specific session details

## Example Usage

### 1. Register and Login
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword"}'

curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword"}'
```

### 2. Upload a Book
```bash
curl -X POST http://localhost:8000/books \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@path/to/book.pdf" \
  -F "title=Example Book" \
  -F "author=Example Author"
```

### 3. Search in the Book
```bash
curl -X POST http://localhost:8000/books/{YOUR_BOOK_ID}/search \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence concepts", "max_results": 5}'
```

## Development Guidelines

### Following Constitution Principles
- All changes must start with a clear specification
- Follow TDD: write tests first, then implementation
- Keep changes small and testable
- Use type hints with Python 3.10+ union syntax (e.g., `str | int`)
- Each commit should reference relevant specs, tasks, or decisions

### Code Structure
- `src/models/` - Data models and database schemas
- `src/services/` - Business logic and service layers
- `src/api/` - API endpoints and request/response handling
- `src/rag/` - Retrieval-Augmented Generation components
- `src/ai/` - AI integration and processing components
- `tests/` - Unit, integration, and contract tests

### Testing Strategy
- Unit tests for individual functions and classes
- Integration tests for API endpoints
- Contract tests to ensure API compliance
- Performance tests for RAG pipeline

## Troubleshooting

### Common Issues
- **API Key Issues**: Ensure GOOGLE_API_KEY is set correctly
- **Database Connection**: Verify DATABASE_URL is configured properly
- **File Upload Issues**: Check if file format is supported (PDF, EPUB, TXT)

### Performance Considerations
- For large books (approaching 700 pages), expect longer initial processing time
- The RAG pipeline performance may vary based on query complexity
- Monitor Gemini API usage to stay within rate limits