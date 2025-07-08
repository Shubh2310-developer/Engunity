"""Supabase authentication API endpoints."""

from fastapi import APIRouter, HTTPException, status, Header, Depends
from typing import Optional

from ...schemas.auth import (
    UserRegister, UserLogin, PasswordResetRequest, PasswordResetConfirm,
    AuthResponse, MessageResponse, RefreshTokenRequest, UpdateProfileRequest,
    UserProfile
)
from ...services.auth_service import SupabaseAuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Dependency to get auth service
def get_auth_service() -> SupabaseAuthService:
    return SupabaseAuthService()

@router.post("/register", response_model=AuthResponse)
async def register(
    user_data: UserRegister,
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """Register a new user with Supabase."""
    result = await auth_service.register_user(user_data)
    
    return AuthResponse(
        user=result["user"],
        session=result["session"]
    )

@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: UserLogin,
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """Login a user with Supabase."""
    result = await auth_service.login_user(credentials)
    
    return AuthResponse(
        user=result["user"],
        session=result["session"]
    )

@router.post("/logout", response_model=MessageResponse)
async def logout(
    authorization: Optional[str] = Header(None),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """Logout a user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    access_token = authorization.split(" ")[1]
    success = await auth_service.logout_user(access_token)
    
    return MessageResponse(
        message="Logged out successfully" if success else "Logout failed",
        success=success
    )

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: PasswordResetRequest,
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """Request password reset email."""
    await auth_service.request_password_reset(request.email)
    
    return MessageResponse(
        message="Password reset link has been sent to your email",
        success=True
    )

@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: PasswordResetConfirm,
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """Reset password with access token."""
    success = await auth_service.update_password(
        request.access_token, 
        request.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset failed"
        )
    
    return MessageResponse(
        message="Password has been reset successfully",
        success=True
    )

@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """Refresh access token."""
    result = await auth_service.refresh_session(request.refresh_token)
    
    return AuthResponse(
        user=result["user"],
        session=result["session"]
    )

@router.get("/me")
async def get_current_user(
    authorization: Optional[str] = Header(None),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """Get current user information."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    access_token = authorization.split(" ")[1]
    user = await auth_service.get_user_by_token(access_token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Get additional profile data
    profile = await auth_service.get_user_profile(user.get("id"))
    
    return {
        "user": user,
        "profile": profile
    }

@router.get("/profile/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: str,
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """Get user profile by ID."""
    profile = await auth_service.get_user_profile(user_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return profile

@router.put("/profile", response_model=MessageResponse)
async def update_profile(
    profile_data: UpdateProfileRequest,
    authorization: Optional[str] = Header(None),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """Update user profile."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    access_token = authorization.split(" ")[1]
    user = await auth_service.get_user_by_token(access_token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    success = await auth_service.update_user_profile(
        user.get("id"), 
        profile_data.dict(exclude_unset=True)
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
    
    return MessageResponse(
        message="Profile updated successfully",
        success=True
    )