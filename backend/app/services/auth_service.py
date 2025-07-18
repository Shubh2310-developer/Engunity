"""Supabase authentication service."""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from supabase import Client

from ..config.database import get_supabase, get_supabase_admin
from ..schemas.auth import UserRegister, UserLogin

class SupabaseAuthService:
    """Service for Supabase authentication operations."""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.admin_client = get_supabase_admin()
    
    async def register_user(self, user_data: UserRegister) -> Dict[str, Any]:
        """Register a new user with Supabase."""
        try:
            # Sign up the user
            response = self.supabase.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password,
                "options": {
                    "data": {
                        "full_name": user_data.full_name,
                        "avatar_url": None
                    }
                }
            })
            
            if response.user is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Registration failed"
                )
            
            return {
                "user": response.user,
                "session": response.session
            }
            
        except Exception as e:
            if "User already registered" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )
    
    async def login_user(self, credentials: UserLogin) -> Dict[str, Any]:
        """Login a user with Supabase."""
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": credentials.email,
                "password": credentials.password
            })
            
            if response.user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            return {
                "user": response.user,
                "session": response.session
            }
            
        except Exception as e:
            if "Invalid login credentials" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login failed"
            )
    
    async def logout_user(self, access_token: str) -> bool:
        """Logout a user by invalidating their session."""
        try:
            # Set the session for the client
            self.supabase.auth.set_session(access_token, None)
            self.supabase.auth.sign_out()
            return True
        except Exception:
            return False
    
    async def get_user_by_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from access token."""
        try:
            import asyncio
            import logging
            logger = logging.getLogger(__name__)
            
            logger.info(f"Validating token with Supabase: {access_token[:20]}...")
            
            # Set the session and get user with timeout
            response = await asyncio.wait_for(
                asyncio.to_thread(self.supabase.auth.get_user, access_token),
                timeout=10.0  # 10 second timeout
            )
            
            if response.user:
                logger.info(f"Token validation successful for user: {getattr(response.user, 'email', 'unknown')}")
                return response.user
            else:
                logger.warning("Token validation failed - no user returned")
                return None
                
        except asyncio.TimeoutError:
            logger.error("Authentication timeout - Supabase took too long to respond")
            return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            # Try alternative validation method
            try:
                logger.info("Trying alternative token validation...")
                # Alternative: try using the token directly with get_session
                self.supabase.auth.set_session(access_token, None)
                session = self.supabase.auth.get_session()
                if session and session.user:
                    logger.info("Alternative validation successful")
                    return session.user
            except Exception as alt_e:
                logger.error(f"Alternative validation also failed: {alt_e}")
            
            return None
    
    async def refresh_session(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh user session."""
        try:
            response = self.supabase.auth.refresh_session(refresh_token)
            
            if response.session is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            return {
                "user": response.user,
                "session": response.session
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token refresh failed"
            )
    
    async def request_password_reset(self, email: str) -> bool:
        """Request password reset email."""
        try:
            response = self.supabase.auth.reset_password_email(
                email,
                {
                    "redirect_to": "http://localhost:3000/reset-password"
                }
            )
            return True
        except Exception:
            # Don't reveal if email exists or not for security
            return True
    
    async def update_password(self, access_token: str, new_password: str) -> bool:
        """Update user password."""
        try:
            # Set the session for the client
            self.supabase.auth.set_session(access_token, None)
            
            response = self.supabase.auth.update_user({
                "password": new_password
            })
            
            return response.user is not None
        except Exception:
            return False
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile data from database."""
        try:
            # Query user profiles table if you have additional user data
            response = self.supabase.table('profiles').select('*').eq('id', user_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception:
            return None
    
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Update user profile data."""
        try:
            response = self.supabase.table('profiles').upsert({
                'id': user_id,
                **profile_data,
                'updated_at': 'now()'
            }).execute()
            
            return len(response.data) > 0
        except Exception:
            return False