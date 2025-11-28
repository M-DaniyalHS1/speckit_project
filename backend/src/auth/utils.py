"""Utility functions for authentication in the AI-Enhanced Interactive Book Agent."""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from backend.src.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against
        
    Returns:
        True if passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a hash for a plain password.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        The hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time for the token
        
    Returns:
        The encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default to 15 minutes if no expiration is specified
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token.
    
    Args:
        data: The data to encode in the token
        
    Returns:
        The encoded JWT token
    """
    to_encode = data.copy()
    
    # Refresh tokens should last longer (e.g., 7 days)
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """Verify a JWT token and return its payload.
    
    Args:
        token: The JWT token to verify
        
    Returns:
        The token's payload if valid
        
    Raises:
        JWTError: If the token is invalid or expired
    """
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    user_id: str = payload.get("sub")
    
    if user_id is None:
        raise JWTError("Token does not contain a valid user ID")
    
    return payload


def get_user_role_from_token(token: str) -> str:
    """Extract the user role from a JWT token.
    
    Args:
        token: The JWT token to extract role from
        
    Returns:
        The user's role, defaults to "user" if not specified
    """
    try:
        payload = verify_token(token)
        return payload.get("role", "user")
    except JWTError:
        return "user"  # Default role if token invalid