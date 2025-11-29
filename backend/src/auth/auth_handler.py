"""Authentication handlers for AI-Enhanced Interactive Book Agent."""
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from backend.src.database import get_db_session
from backend.src.models.sqlalchemy_models import User
from backend.src.auth.schemas import UserCreate, UserLogin, Token
from backend.src.auth.security import get_password_hash, verify_password, create_access_token
from backend.src.config import settings


# Create API router
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}}
)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db_session)):
    """Register a new user with the provided credentials."""
    # Hash the password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user instance
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        preferences=user_data.preferences
    )
    
    # Add to database
    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id)},
        expires_delta=access_token_expires
    )
    
    # Create refresh token if needed
    refresh_token_expires = timedelta(days=settings.jwt_refresh_token_expire_days)
    refresh_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id)},
        expires_delta=refresh_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
        expires_in=access_token_expires.seconds
    )


@router.post("/login", response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db_session)):
    """Authenticate user and return access token."""
    # Query user by email
    result = await db.execute(select(User).filter(User.email == form_data.username))
    user = result.scalars().first()
    
    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id)},
        expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token_expires = timedelta(days=settings.jwt_refresh_token_expire_days)
    refresh_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id)},
        expires_delta=refresh_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
        expires_in=access_token_expires.seconds
    )


@router.post("/logout")
async def logout_user():
    """Logout the current user (client-side token removal)."""
    # In a stateless JWT system, logout is typically handled client-side
    # by removing the token from storage. Optionally, we could implement
    # a token blacklist mechanism for server-side logout.
    return {"message": "Successfully logged out"}