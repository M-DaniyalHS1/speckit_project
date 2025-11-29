"""SQLAlchemy models for the AI-Enhanced Interactive Book Agent."""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid
from backend.src.database import Base


class User(Base):
    """SQLAlchemy model for users in the database."""
    __tablename__ = "users"

    # Primary key with UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User information
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)

    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Preferences and settings
    preferences = Column(Text, default='{}')  # JSON stored as text

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Book(Base):
    """SQLAlchemy model for books in the database."""
    __tablename__ = "books"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Book information
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_format = Column(String(10), nullable=False)  # pdf, epub, docx, txt
    file_size = Column(Integer, nullable=True)  # Size in bytes
    total_pages = Column(Integer, nullable=True)

    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ReadingSession(Base):
    """SQLAlchemy model for reading sessions in the database."""
    __tablename__ = "reading_sessions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=False)

    # Session information
    current_location = Column(String(100), nullable=False)  # chapter:page:paragraph
    current_position_percent = Column(Integer, nullable=True)  # 0-100 percentage

    # Session metadata
    started_at = Column(DateTime, server_default=func.now())
    last_accessed_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)


class BookContent(Base):
    """SQLAlchemy model for book content chunks in the database."""
    __tablename__ = "book_contents"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to book
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=False)

    # Content information
    chunk_id = Column(String(100), nullable=False)  # Identifier for this chunk
    content = Column(Text, nullable=False)  # The actual text content
    page_number = Column(Integer, nullable=True)  # Page where this content appears
    section_title = Column(String(255), nullable=True)  # Section/chapter title
    chapter = Column(String(100), nullable=True)  # Chapter name or number

    # Vector embedding reference (for similarity search)
    embedding_id = Column(String(255), nullable=True)  # Reference to vector DB

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Query(Base):
    """SQLAlchemy model for user queries in the database."""
    __tablename__ = "queries"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=True)  # Optional for global queries

    # Query information
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50), nullable=False)  # search, explanation, summary, etc.
    context = Column(Text, nullable=True)  # Additional context information

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())


class Explanation(Base):
    """SQLAlchemy model for explanations in the database."""
    __tablename__ = "explanations"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to query
    query_id = Column(UUID(as_uuid=True), ForeignKey("queries.id"), nullable=False)

    # Foreign key to book content (for context)
    content_id = Column(UUID(as_uuid=True), ForeignKey("book_contents.id"), nullable=True)

    # Explanation information
    explanation_text = Column(Text, nullable=False)
    complexity_level = Column(String(20), nullable=False)  # simple, detailed, technical
    sources = Column(Text, nullable=True)  # JSON string of sources referenced

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class LearningMaterial(Base):
    """SQLAlchemy model for learning materials in the database."""
    __tablename__ = "learning_materials"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to user and book
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=False)

    # Material information
    material_type = Column(String(50), nullable=False)  # quiz, flashcard, note, summary
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # The actual material content
    additional_metadata = Column(Text, nullable=True)  # JSON string of additional metadata

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())