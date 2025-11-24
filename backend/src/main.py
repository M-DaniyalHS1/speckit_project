"""Main application entry point for the AI-Enhanced Interactive Book Agent.

This FastAPI application serves as the backend for the book agent system,
providing APIs for reading progress tracking, semantic search, content
explanation, summarization, and learning tools.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import API routers
from backend.src.api import sessions, books, search, explanations, summaries, learning_tools
from backend.src.config import settings

# Create the main FastAPI application
app = FastAPI(
    title="AI-Enhanced Interactive Book Agent",
    description="An AI-powered reading companion with progress tracking, search, explanations, and learning tools",
    version="0.1.0",
    # Add additional metadata from settings if needed
)

# Add CORS middleware to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(sessions.router, prefix="/api/v1", tags=["sessions"])
app.include_router(books.router, prefix="/api/v1", tags=["books"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(explanations.router, prefix="/api/v1", tags=["explanations"])
app.include_router(summaries.router, prefix="/api/v1", tags=["summaries"])
app.include_router(learning_tools.router, prefix="/api/v1", tags=["learning-tools"])

@app.get("/")
def read_root():
    """Root endpoint to confirm the API is running."""
    return {"message": "AI-Enhanced Interactive Book Agent API is running!"}

@app.get("/health")
def health_check():
    """Health check endpoint to verify the application is operational."""
    return {"status": "healthy"}

def main():
    """Main entry point to run the application."""
    uvicorn.run(
        "backend.src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Enable auto-reload during development
    )

if __name__ == "__main__":
    main()