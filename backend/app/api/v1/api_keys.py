"""API Key management endpoints."""

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...core.deps import get_db, get_current_user
from ...models.user import User
from ...services.api_key_service import APIKeyService
from ...schemas.api_key import APIKeyCreate, APIKeyUpdate, APIKeyResponse, ProvidersResponse, BulkValidationResponse

router = APIRouter(prefix="/api-keys", tags=["api-keys"])

@router.get("/providers", response_model=ProvidersResponse)
async def get_supported_providers(
    db: Session = Depends(get_db)
):
    """Get information about all supported providers."""
    service = APIKeyService(db)
    providers = service.get_provider_info()
    return {"providers": providers}

@router.get("/", response_model=List[APIKeyResponse])
async def get_user_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all API keys for the current user."""
    service = APIKeyService(db)
    api_keys = await service.get_user_api_keys(current_user.id)
    return api_keys

@router.post("/", response_model=APIKeyResponse)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update an API key for a provider."""
    service = APIKeyService(db)
    
    try:
        result = await service.save_api_key(
            user_id=current_user.id,
            provider=api_key_data.provider,
            api_key=api_key_data.api_key,
            model_name=api_key_data.model_name,
            is_default=api_key_data.is_default
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save API key"
        )

@router.put("/{api_key_id}", response_model=APIKeyResponse)
async def update_api_key(
    api_key_id: int,
    api_key_data: APIKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing API key."""
    service = APIKeyService(db)
    
    try:
        # First verify the key belongs to the user
        user_keys = await service.get_user_api_keys(current_user.id)
        if not any(key["id"] == api_key_id for key in user_keys):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        # Update the key
        result = await service.save_api_key(
            user_id=current_user.id,
            provider=api_key_data.provider,
            api_key=api_key_data.api_key,
            model_name=api_key_data.model_name,
            is_default=api_key_data.is_default
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update API key"
        )

@router.delete("/{api_key_id}")
async def delete_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an API key."""
    service = APIKeyService(db)
    
    success = await service.delete_api_key(current_user.id, api_key_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return {"message": "API key deleted successfully"}

@router.post("/{api_key_id}/validate")
async def validate_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate an API key by testing it with the provider."""
    service = APIKeyService(db)
    
    # First verify the key belongs to the user
    user_keys = await service.get_user_api_keys(current_user.id)
    if not any(key["id"] == api_key_id for key in user_keys):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    is_valid = await service.validate_api_key(api_key_id)
    return {"is_valid": is_valid}

@router.post("/{api_key_id}/set-default")
async def set_default_provider(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set a provider as the default."""
    service = APIKeyService(db)
    
    success = await service.set_default_provider(current_user.id, api_key_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return {"message": "Default provider set successfully"}

@router.post("/{api_key_id}/toggle")
async def toggle_provider(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle a provider's active status."""
    service = APIKeyService(db)
    
    success = await service.toggle_provider(current_user.id, api_key_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return {"message": "Provider status toggled successfully"}

@router.get("/working-key/{provider}")
async def get_working_key(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a working API key for a specific provider (for internal use)."""
    service = APIKeyService(db)
    
    try:
        api_key, used_provider = await service.get_working_api_key(current_user.id, provider)
        return {
            "provider": used_provider,
            "has_key": True,
            "is_fallback": False
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No working API key found for provider: {provider}"
        )
@router.post("/validate-all", response_model=BulkValidationResponse)
async def bulk_validate_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk validate all of a user's API keys."""
    service = APIKeyService(db)
    results = await service.bulk_validate_user_api_keys(current_user.id)
    return {"results": results}