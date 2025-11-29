"""Database connection setup for the AI-Enhanced Interactive Book Agent.

This module configures the PostgreSQL database connection using SQLAlchemy
with proper connection pooling and async support for high concurrency.
"""
from sqlalchemy.ext.declarative import declarative_base
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
from urllib.parse import quote_plus


# Load database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://username:password@localhost/book_agent_db")

# Quote the password in case it contains special characters
if DATABASE_URL.startswith("postgresql+asyncpg://") or DATABASE_URL.startswith("postgresql://"):
    # Parse the URL to extract components
    from urllib.parse import urlparse
    parsed = urlparse(DATABASE_URL)
    # Reconstruct with properly quoted password
    password_quoted = quote_plus(parsed.password) if parsed.password else ""
    username = parsed.username if parsed.username else ""
    hostname = parsed.hostname if parsed.hostname else ""
    port = f":{parsed.port}" if parsed.port else ""
    database = parsed.path[1:] if parsed.path else ""

    if not DATABASE_URL.startswith("postgresql+asyncpg://"):
        # Convert to asyncpg driver if not already specified
        DATABASE_URL = f"postgresql+asyncpg://{username}:{password_quoted}@{hostname}{port}/{database}"


# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    pool_size=20,  # Base pool size for handling 600 concurrent users efficiently
    max_overflow=30,  # Additional connections beyond pool_size
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False  # Set to True for SQL query logging (useful for debugging)
)

# Create async sessionmaker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create base class for SQLAlchemy models
Base = declarative_base()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency function to get database session for FastAPI endpoints.

    This function provides database sessions to API endpoints and ensures
    proper cleanup after each request.

    Yields:
        AsyncSession: An asynchronous database session

    Example:
        # In a FastAPI endpoint:
        async def some_endpoint(db: AsyncSession = Depends(get_db_session)):
            # Work with the database session
            pass
    """
    async with AsyncSessionLocal() as session:
        yield session
        # Session is automatically closed after the request