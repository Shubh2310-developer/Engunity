"""Supabase authentication schemas."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# User Registration
class UserRegister(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)

# User Login
class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str
    remember_me: bool = False

# Password Reset Request
class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr

# Password Reset Confirm
class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    access_token: str
    new_password: str = Field(..., min_length=8, max_length=128)

# Refresh Token Request
class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str

# Supabase User Response
class SupabaseUser(BaseModel):
    """Schema for Supabase user response."""
    id: str
    email: str
    email_confirmed_at: Optional[str] = None
    phone: Optional[str] = None
    phone_confirmed_at: Optional[str] = None
    confirmed_at: Optional[str] = None
    last_sign_in_at: Optional[str] = None
    created_at: str
    updated_at: str
    user_metadata: Dict[str, Any] = {}
    app_metadata: Dict[str, Any] = {}

# Supabase Session Response
class SupabaseSession(BaseModel):
    """Schema for Supabase session response."""
    access_token: str
    refresh_token: str
    expires_in: int
    expires_at: int
    token_type: str = "bearer"
    user: SupabaseUser

# Authentication Response
class AuthResponse(BaseModel):
    """Schema for authentication response."""
    user: SupabaseUser
    session: SupabaseSession

# User Profile
class UserProfile(BaseModel):
    """Schema for user profile data."""
    id: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    organization: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# Update Profile Request
class UpdateProfileRequest(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    organization: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None

# Message Response
class MessageResponse(BaseModel):
    """Schema for general message response."""
    message: str
    success: bool = True