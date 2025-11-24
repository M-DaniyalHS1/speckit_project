# AI-Enhanced Interactive Book Agent

An AI-powered reading companion that helps users engage with book content through progress tracking, semantic search, content explanations, summarization, and learning tools.

## Features

- **Reading Companion**: Track reading progress and resume from where you left off
- **Semantic Search**: Find relevant passages across the entire book using natural language queries
- **Content Explanations**: Get AI-powered explanations of complex concepts in simpler language
- **Summarization & Notes**: Generate chapter summaries and take structured notes
- **Learning Tools**: Create quizzes and flashcards from book content

## Technologies

- **Backend**: FastAPI, SQLAlchemy, Langchain
- **AI/ML**: Google Generative AI (Gemini), ChromaDB for vector storage
- **Frontend**: React (planned)
- **Database**: PostgreSQL

## Setup

### Prerequisites

- Python 3.12+
- Poetry (recommended) or pip
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd book-agent
   ```

2. Set up the virtual environment:
   ```bash
   # Using the provided script (Unix/Mac):
   ./setup-venv.sh
   
   # Or using the PowerShell script (Windows):
   .\setup-venv.ps1
   
   # Or manually:
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your actual configuration
   ```

4. Run the application:
   ```bash
   # Using Poetry:
   poetry run python -m backend.src.main
   
   # Or directly:
   python -m backend.src.main
   ```

## Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env` and update with your specific settings.

## Project Structure

```
book-agent/
├── backend/
│   ├── src/
│   │   ├── models/      # Pydantic models
│   │   ├── services/    # Business logic
│   │   ├── api/         # API endpoints
│   │   ├── rag/         # RAG components
│   │   ├── ai/          # AI integration
│   │   └── auth/        # Authentication
│   └── tests/           # Test files
├── frontend/            # React frontend (planned)
├── docs/                # Documentation
├── specs/               # Feature specifications
└── history/             # Project history
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

[License information to be added]