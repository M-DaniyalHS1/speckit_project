"""Email verification functionality for the AI-Enhanced Interactive Book Agent.

This module handles email verification for user accounts using JWT tokens
and provides utilities for sending verification emails.
"""
import asyncio
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from jose import jwt, JWTError
from backend.src.config import settings
from backend.src.auth.utils import create_access_token
from backend.src.models.sqlalchemy_models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


class EmailVerificationService:
    """Service for handling email verification functionality."""
    
    def __init__(self):
        """Initialize the email verification service."""
        self.verification_token_expire_minutes = 24 * 60  # 24 hours
    
    def create_verification_token(self, email: str) -> str:
        """Create a JWT token for email verification.
        
        Args:
            email: Email address to verify
            
        Returns:
            JWT token for email verification
        """
        data = {
            "email": email,
            "type": "email_verification",
        }
        expire = datetime.utcnow() + timedelta(minutes=self.verification_token_expire_minutes)
        data.update({"exp": expire})
        
        return jwt.encode(data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    
    def verify_verification_token(self, token: str) -> Optional[str]:
        """Verify the email verification token and return the email if valid.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Email address if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            token_type = payload.get("type")
            
            if token_type != "email_verification":
                return None
                
            email = payload.get("email")
            if email is None:
                return None
                
            return email
        except JWTError:
            return None
    
    async def send_verification_email(self, email: str, verification_token: str) -> bool:
        """Send a verification email to the specified email address.
        
        Args:
            email: Recipient email address
            verification_token: Verification token to include in the email
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = settings.email_from
            msg['To'] = email
            msg['Subject'] = "Verify Your Email Address"
            
            # Create verification link
            verification_link = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
            
            # Email body
            body = f"""
            <html>
                <body>
                    <h2>Email Verification</h2>
                    <p>Hello,</p>
                    <p>Please click the link below to verify your email address:</p>
                    <p><a href="{verification_link}">Verify Email</a></p>
                    <p>If you did not create an account with us, please ignore this email.</p>
                    <p>This link will expire in 24 hours.</p>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Connect to server and send email
            server = smtplib.SMTP(settings.email_host, settings.email_port)
            server.starttls()  # Enable encryption
            server.login(settings.email_username, settings.email_password)
            
            text = msg.as_string()
            server.sendmail(settings.email_from, email, text)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Error sending verification email: {str(e)}")
            return False
    
    async def mark_email_verified(self, db: AsyncSession, email: str) -> bool:
        """Mark a user's email as verified in the database.
        
        Args:
            db: Database session
            email: Email address to mark as verified
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find the user by email
            result = await db.execute(select(User).filter(User.email == email))
            user = result.scalars().first()
            
            if not user:
                return False
            
            # Update the verification status
            user.is_verified = True
            
            # Commit the changes
            await db.commit()
            await db.refresh(user)
            
            return True
        except Exception as e:
            print(f"Error marking email as verified: {str(e)}")
            await db.rollback()
            return False


class TempEmailStorage:
    """Temporary storage for unverified email changes (for GDPR compliance)."""
    
    def __init__(self):
        """Initialize temporary storage for email changes."""
        self.pending_changes = {}  # In a real app, use a database
    
    async def store_pending_email_change(self, user_id: str, new_email: str) -> str:
        """Store a pending email change and return a verification token.
        
        Args:
            user_id: ID of the user requesting the change
            new_email: New email address
            
        Returns:
            Verification token for the new email
        """
        verification_token = jwt.encode(
            {
                "user_id": user_id,
                "new_email": new_email,
                "type": "email_change_verification",
                "exp": datetime.utcnow() + timedelta(minutes=24 * 60)  # 24 hours
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        
        self.pending_changes[verification_token] = {
            "user_id": user_id,
            "new_email": new_email,
            "created_at": datetime.utcnow()
        }
        
        return verification_token
    
    async def process_email_change(self, db: AsyncSession, verification_token: str) -> bool:
        """Process a pending email change after verification.
        
        Args:
            db: Database session
            verification_token: Verification token for the email change
            
        Returns:
            True if successful, False otherwise
        """
        if verification_token not in self.pending_changes:
            return False
        
        change_request = self.pending_changes[verification_token]
        user_id = change_request["user_id"]
        new_email = change_request["new_email"]
        
        try:
            # Find the user by ID
            result = await db.execute(select(User).filter(User.id == user_id))
            user = result.scalars().first()
            
            if not user:
                return False
            
            # Update the email
            user.email = new_email
            user.is_verified = True  # New email is now verified
            
            # Commit the changes
            await db.commit()
            await db.refresh(user)
            
            # Remove the pending change
            del self.pending_changes[verification_token]
            
            return True
        except Exception as e:
            print(f"Error processing email change: {str(e)}")
            await db.rollback()
            return False


# Global instance of the email verification service
email_verification_service = EmailVerificationService()
temp_email_storage = TempEmailStorage()