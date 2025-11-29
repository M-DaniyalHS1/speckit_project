"""Authentication handlers for the AI-Enhanced Interactive Book Agent.

This module implements OAuth2 with JWT tokens for secure authentication
using FastAPI's Security features.
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from jose import JWTError, jwt
from backend.src.models.user import User  # Adjust import based on actual User model location
from backend.src.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.src.auth.utils import verify_password, create_access_token, create_refresh_token, get_password_hash
from backend.src.config import settings


router = APIRouter(prefix="/auth", tags=["auth"])


# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class Token(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None


class UserLogin(BaseModel):
    """User login request model."""
    email: str
    password: str


class UserRegister(BaseModel):
    """User registration request model."""
    email: str
    password: str
    first_name: str
    last_name: str


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """Get the current authenticated user from the token.
    
    Args:
        token: JWT token from the request
        db: Database session
        
    Returns:
        The authenticated user object
        
    Raises:
        HTTPException: If token is invalid or user doesn't exist
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    # Fetch user from database
    result = await db.execute(select(User).filter(User.email == token_data.username))
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
    
    return user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session)
):
    """Authenticate user and return JWT tokens.
    
    Args:
        request: The incoming request
        form_data: Login credentials (username/email and password)
        db: Database session
        
    Returns:
        Token containing access and refresh tokens
    """
    # Fetch user from database
    result = await db.execute(select(User).filter(User.email == form_data.username))
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id), "role": "user"},
        expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": str(user.id)}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/register")
async def register(
    request: Request,
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db_session)
):
    """Register a new user.
    
    Args:
        request: The incoming request
        user_data: Registration data
        db: Database session
        
    Returns:
        Success message
    """
    from backend.src.models.sqlalchemy_models import User  # Import here to avoid circular imports
    
    # Check if user already exists
    result = await db.execute(select(User).filter(User.email == user_data.email))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return {"message": "User registered successfully"}


@router.post("/refresh")
async def refresh_token(
    request: Request,
    token: str
):
    """Refresh the access token using the refresh token.
    
    Args:
        request: The incoming request
        token: Refresh token
        
    Returns:
        New access token
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify token type
        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        new_access_token = create_access_token(
            data={"sub": username, "user_id": user_id, "role": "user"},
            expires_delta=access_token_expires
        )
        
        return {"access_token": new_access_token, "token_type": "bearer"}
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )