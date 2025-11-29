"""Configuration module for the AI-Enhanced Interactive Book Agent.

This module handles loading and validation of environment variables
that configure the application's behavior.
"""
import os
from typing import Optional
from pydantic import BaseModel, validator
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


class Settings(BaseModel):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "postgresql://username:password@localhost/book_agent_db")
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "20"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "30"))
    
    # AI/ML Configuration
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    gemini_model_name: str = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
    
    # Authentication Configuration
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-default-dev-key-change-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    jwt_refresh_token_expire_days: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Vector Database Configuration
    chromadb_path: str = os.getenv("CHROMADB_PATH", "./chroma_data")
    
    # Application Configuration
    max_book_pages: int = int(os.getenv("MAX_BOOK_PAGES", "700"))
    max_concurrent_users: int = int(os.getenv("MAX_CONCURRENT_USERS", "600"))
    book_upload_size_limit: str = os.getenv("BOOK_UPLOAD_SIZE_LIMIT", "50MB")
    allowed_book_extensions: str = os.getenv("ALLOWED_BOOK_EXTENSIONS", "pdf,docx,epub,txt")
    
    # Security Configuration
    encrypt_password_algorithm: str = os.getenv("ENCRYPT_PASSWORD_ALGORITHM", "bcrypt")
    enforce_https: bool = os.getenv("ENFORCE_HTTPS", "false").lower() == "true"
    
    # API Configuration
    api_rate_limit: int = int(os.getenv("API_RATE_LIMIT", "100"))
    enable_api_logging: bool = os.getenv("ENABLE_API_LOGGING", "true").lower() == "true"
    
    # Email Configuration
    email_host: str = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    email_port: int = int(os.getenv("EMAIL_PORT", "587"))
    email_username: str = os.getenv("EMAIL_USERNAME", "")
    email_password: str = os.getenv("EMAIL_PASSWORD", "")
    email_from: str = os.getenv("EMAIL_FROM", "")
    
    # External Services
    external_api_timeout: int = int(os.getenv("EXTERNAL_API_TIMEOUT", "30"))
    
    @validator('google_api_key')
    def validate_google_api_key(cls, v):
        """Validate that Google API key is set."""
        if not v:
            raise ValueError('GOOGLE_API_KEY must be set in environment variables')
        return v
    
    @validator('database_url')
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://')):
            raise ValueError('DATABASE_URL must use PostgreSQL protocol')
        return v
    
    @property
    def allowed_extensions_list(self) -> list:
        """Return allowed book extensions as a list."""
        return [ext.strip() for ext in self.allowed_book_extensions.split(',')]
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True


# Create a singleton instance of settings
settings = Settings()