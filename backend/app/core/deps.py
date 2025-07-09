"""Core dependencies for the application."""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from ..config.database import SessionLocal
from ..models.user import User
from ..services.auth_service import SupabaseAuthService

def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Extract token from header
        token = authorization.split(" ")[1]
        
        # Initialize auth service
        auth_service = SupabaseAuthService()
        
        # Get user from Supabase
        user_data = await auth_service.get_user_by_token(token)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get or create user in local database
        user = db.query(User).filter(User.email == user_data.get("email")).first()
        if not user:
            # Create user if doesn't exist
            user = User(
                email=user_data.get("email"),
                full_name=user_data.get("user_metadata", {}).get("full_name", ""),
                hashed_password="",  # Not used for Supabase users
                is_active=True,
                is_verified=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )