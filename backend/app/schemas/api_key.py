"""API Key schemas for request/response validation."""

from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field, validator

class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""
    provider: str = Field(..., description="Provider name (openai, gemini, together, openrouter, huggingface)")
    api_key: str = Field(..., description="API key value")
    model_name: Optional[str] = Field(None, description="Default model for this provider")
    is_default: bool = Field(False, description="Set as default provider")
    
    @validator('provider')
    def validate_provider(cls, v):
        allowed_providers = ["openai", "gemini", "together", "openrouter", "huggingface"]
        if v not in allowed_providers:
            raise ValueError(f"Provider must be one of: {allowed_providers}")
        return v
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("API key cannot be empty")
        return v.strip()

class APIKeyUpdate(BaseModel):
    """Schema for updating an API key."""
    provider: str = Field(..., description="Provider name")
    api_key: str = Field(..., description="API key value")
    model_name: Optional[str] = Field(None, description="Default model for this provider")
    is_default: bool = Field(False, description="Set as default provider")
    
    @validator('provider')
    def validate_provider(cls, v):
        allowed_providers = ["openai", "gemini", "together", "openrouter", "huggingface"]
        if v not in allowed_providers:
            raise ValueError(f"Provider must be one of: {allowed_providers}")
        return v
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("API key cannot be empty")
        return v.strip()

class APIKeyResponse(BaseModel):
    """Schema for API key response."""
    id: int
    provider: str
    model_name: Optional[str]
    is_active: bool
    is_default: bool
    is_valid: bool
    last_validated: Optional[datetime]
    usage_count: int
    last_used: Optional[datetime]
    created_at: datetime
    provider_info: Dict
    
    class Config:
        from_attributes = True

class ProviderInfo(BaseModel):
    """Schema for provider information."""
    name: str
    models: list
    default_model: str
    api_base: str
    docs_url: str
    signup_url: str

class ProvidersResponse(BaseModel):
    """Schema for providers response."""
    providers: Dict[str, ProviderInfo]

class APIKeyStatus(BaseModel):
    """Schema for API key status."""
    has_key: bool
    provider: str
    is_fallback: bool = False
class APIKeyValidationStatus(BaseModel):
    """Schema for the validation status of a single API key."""
    id: int
    provider: str
    is_valid: bool
    error_message: Optional[str]

class BulkValidationResponse(BaseModel):
    """Schema for the bulk validation response."""
    results: List[APIKeyValidationStatus]