"""Test configuration for the AI-Enhanced Interactive Book Agent.

This module sets up test fixtures, configurations, and utilities for testing.
"""
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from backend.src.database import Base


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine


@pytest.fixture(scope="session")
async def test_db_session(test_db_engine):
    """Create a test database session."""
    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create an async session
    async_session = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture
def api_client():
    """Create a test API client."""
    from fastapi.testclient import TestClient
    from backend.src.main import app

    # Note: For testing API endpoints that require a database,
    # you'll need to override the database dependency separately in each test

    with TestClient(app) as client:
        yield client


# Test utility functions
def create_test_user():
    """Create a test user for integration tests."""
    pass  # Implementation would go here


def create_test_book(user_id: str):
    """Create a test book for integration tests."""
    pass  # Implementation would go here