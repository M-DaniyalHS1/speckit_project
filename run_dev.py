"""Development script to run the AI-Enhanced Interactive Book Agent."""
import uvicorn
from backend.src.main import app


def main():
    """Main entry point to run the application."""
    uvicorn.run(
        "backend.src.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["backend/src"],
        log_level="info"
    )


if __name__ == "__main__":
    main()