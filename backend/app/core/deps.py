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
    import logging
    logger = logging.getLogger(__name__)
    
    if not authorization:
        logger.warning("No authorization header provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authorization header provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not authorization.startswith("Bearer "):
        logger.warning(f"Invalid authorization header format: {authorization[:50]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Extract token from header
        token = authorization.split(" ")[1]
        logger.info(f"Attempting to authenticate with token: {token[:20]}...")
        
        # Initialize auth service
        auth_service = SupabaseAuthService()
        
        # Get user from Supabase
        user_data = await auth_service.get_user_by_token(token)
        if not user_data:
            logger.warning("Failed to get user data from Supabase")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract user email safely
        user_email = getattr(user_data, 'email', None)
        if not user_email:
            logger.warning("No email found in user data")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user data",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"Successfully authenticated user: {user_email}")
        
        # Get or create user in local database
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            logger.info(f"Creating new user: {user_email}")
            # Create user if doesn't exist
            user_metadata = getattr(user_data, 'user_metadata', {})
            full_name = user_metadata.get('full_name', '') if isinstance(user_metadata, dict) else ''
            
            user = User(
                email=user_email,
                full_name=full_name,
                hashed_password="",  # Not used for Supabase users
                is_active=True,
                is_verified=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )