"""API Key service for managing user API keys."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
from ..models.api_key import APIKey, DefaultAPIKey
from ..models.user import User
from ..utils.crypto import encrypt_text, decrypt_text
from ..config.settings import get_settings

logger = logging.getLogger(__name__)

class APIKeyService:
    """Service for managing API keys."""
    
    
    # Supported providers
    SUPPORTED_PROVIDERS = {
        "openai": {
            "name": "OpenAI",
            "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            "default_model": "gpt-4",
            "api_base": "https://api.openai.com/v1",
            "docs_url": "https://platform.openai.com/docs/api-reference",
            "signup_url": "https://platform.openai.com/signup"
        },
        "gemini": {
            "name": "Google Gemini",
            "models": ["gemini-pro", "gemini-pro-vision"],
            "default_model": "gemini-pro",
            "api_base": "https://generativelanguage.googleapis.com/v1",
            "docs_url": "https://ai.google.dev/docs",
            "signup_url": "https://makersuite.google.com/"
        },
        "together": {
            "name": "Together.ai",
            "models": ["meta-llama/Llama-2-70b-chat-hf", "mistralai/Mixtral-8x7B-Instruct-v0.1"],
            "default_model": "meta-llama/Llama-2-70b-chat-hf",
            "api_base": "https://api.together.xyz/v1",
            "docs_url": "https://docs.together.ai/docs",
            "signup_url": "https://together.ai/"
        },
        "openrouter": {
            "name": "OpenRouter",
            "models": ["openai/gpt-4", "anthropic/claude-3-sonnet", "google/gemini-pro"],
            "default_model": "openai/gpt-4",
            "api_base": "https://openrouter.ai/api/v1",
            "docs_url": "https://openrouter.ai/docs",
            "signup_url": "https://openrouter.ai/"
        },
        "huggingface": {
            "name": "Hugging Face",
            "models": ["microsoft/DialoGPT-large", "facebook/blenderbot-3B"],
            "default_model": "microsoft/DialoGPT-large",
            "api_base": "https://api-inference.huggingface.co",
            "docs_url": "https://huggingface.co/docs/api-inference",
            "signup_url": "https://huggingface.co/join"
        },
        "groq": {
            "name": "Groq",
            "models": ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma-7b-it"],
            "default_model": "llama-3.3-70b-versatile",
            "api_base": "https://api.groq.com/openai/v1",
            "docs_url": "https://console.groq.com/docs",
            "signup_url": "https://console.groq.com/"
        },
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
    
    async def get_user_api_keys(self, user_id: int) -> List[Dict]:
        """Get all API keys for a user."""
        api_keys = self.db.query(APIKey).filter(APIKey.user_id == user_id).all()
        
        result = []
        for key in api_keys:
            result.append({
                "id": key.id,
                "provider": key.provider,
                "model_name": key.model_name,
                "is_active": key.is_active,
                "is_default": key.is_default,
                "is_valid": key.is_valid,
                "last_validated": key.last_validated,
                "usage_count": key.usage_count,
                "last_used": key.last_used,
                "created_at": key.created_at,
                "provider_info": self.SUPPORTED_PROVIDERS.get(key.provider, {})
            })
        
        return result
    
    async def save_api_key(self, user_id: int, provider: str, api_key: str, 
                          model_name: Optional[str] = None, is_default: bool = False) -> Dict:
        """Save or update an API key for a user."""
        if provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")
        
        # Encrypt the API key
        encrypted_key = encrypt_text(api_key)
        
        # Check if key already exists
        existing_key = self.db.query(APIKey).filter(
            APIKey.user_id == user_id,
            APIKey.provider == provider
        ).first()
        
        if existing_key:
            # Update existing key
            existing_key.api_key = encrypted_key
            existing_key.model_name = model_name or self.SUPPORTED_PROVIDERS[provider]["default_model"]
            existing_key.is_default = is_default
            existing_key.is_valid = False  # Reset validation
            existing_key.updated_at = datetime.utcnow()
            api_key_obj = existing_key
        else:
            # Create new key
            api_key_obj = APIKey(
                user_id=user_id,
                provider=provider,
                api_key=encrypted_key,
                model_name=model_name or self.SUPPORTED_PROVIDERS[provider]["default_model"],
                is_default=is_default
            )
            self.db.add(api_key_obj)
        
        # If this is set as default, unset others
        if is_default:
            self.db.query(APIKey).filter(
                APIKey.user_id == user_id,
                APIKey.id != api_key_obj.id
            ).update({"is_default": False})
        
        self.db.commit()
        self.db.refresh(api_key_obj)
        
        # Validate the key asynchronously
        await self.validate_api_key(api_key_obj.id)
        
        return {
            "id": api_key_obj.id,
            "provider": api_key_obj.provider,
            "model_name": api_key_obj.model_name,
            "is_active": api_key_obj.is_active,
            "is_default": api_key_obj.is_default,
            "is_valid": api_key_obj.is_valid
        }
    
    async def validate_api_key(self, api_key_id: int) -> bool:
        """Validate an API key by making a test request."""
        api_key_obj = self.db.query(APIKey).filter(APIKey.id == api_key_id).first()
        if not api_key_obj:
            return False
        
        try:
            decrypted_key = decrypt_text(api_key_obj.api_key)
            provider = api_key_obj.provider
            
            # Test the API key based on provider
            is_valid = await self._test_provider_key(provider, decrypted_key)
            
            # Update validation status
            api_key_obj.is_valid = is_valid
            api_key_obj.last_validated = datetime.utcnow()
            api_key_obj.validation_error = None if is_valid else "Invalid API key"
            
            self.db.commit()
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating API key {api_key_id}: {str(e)}")
            api_key_obj.is_valid = False
            api_key_obj.validation_error = str(e)
            self.db.commit()
            return False
    
    async def _test_provider_key(self, provider: str, api_key: str) -> bool:
        """Test an API key for a specific provider."""
        try:
            if provider == "openai":
                import openai
                openai.api_key = api_key
                # Test with a simple completion
                response = await openai.ChatCompletion.acreate(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=1
                )
                return True
                
            elif provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content("Hello")
                return True
                
            elif provider == "together":
                import together
                together.api_key = api_key
                response = together.Complete.create(
                    model="meta-llama/Llama-2-70b-chat-hf",
                    prompt="Hello",
                    max_tokens=1
                )
                return True
                
            elif provider == "openrouter":
                import openai
                openai.api_key = api_key
                openai.api_base = "https://openrouter.ai/api/v1"
                response = await openai.ChatCompletion.acreate(
                    model="openai/gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=1
                )
                return True
                
            elif provider == "huggingface":
                import requests
                headers = {"Authorization": f"Bearer {api_key}"}
                response = requests.post(
                    "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large",
                    headers=headers,
                    json={"inputs": "Hello"}
                )
                return response.status_code == 200
                
            elif provider == "groq":
                from groq import Groq
                client = Groq(api_key=api_key)
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=1
                )
                return True
                
        except Exception as e:
            logger.error(f"Error testing {provider} API key: {str(e)}")
            return False
        
        return False
    
    async def get_working_api_key(self, user_id: int, provider: Optional[str] = None) -> Tuple[str, str]:
        """Get a working API key for a user or fallback to default."""
        # First try user's keys
        if provider:
            # Get specific provider key
            user_key = self.db.query(APIKey).filter(
                APIKey.user_id == user_id,
                APIKey.provider == provider,
                APIKey.is_active == True,
                APIKey.is_valid == True
            ).first()
            
            if user_key:
                return decrypt_text(user_key.api_key), provider
        else:
            # Get default provider key
            user_key = self.db.query(APIKey).filter(
                APIKey.user_id == user_id,
                APIKey.is_active == True,
                APIKey.is_valid == True,
                APIKey.is_default == True
            ).first()
            
            if user_key:
                return decrypt_text(user_key.api_key), user_key.provider
        
        # Fallback to default keys from settings for Groq
        if provider == "groq" or provider is None:
            from ..config.settings import settings
            if settings.groq_api_key:
                return settings.groq_api_key, "groq"
            elif settings.fallback_groq_keys:
                import random
                return random.choice(settings.fallback_groq_keys), "groq"
        
        raise ValueError("No working API key found")
    
    async def delete_api_key(self, user_id: int, api_key_id: int) -> bool:
        """Delete an API key."""
        api_key = self.db.query(APIKey).filter(
            APIKey.id == api_key_id,
            APIKey.user_id == user_id
        ).first()
        
        if not api_key:
            return False
        
        self.db.delete(api_key)
        self.db.commit()
        return True
    
    async def set_default_provider(self, user_id: int, api_key_id: int) -> bool:
        """Set a provider as default."""
        # Unset all defaults
        self.db.query(APIKey).filter(APIKey.user_id == user_id).update({"is_default": False})
        
        # Set new default
        api_key = self.db.query(APIKey).filter(
            APIKey.id == api_key_id,
            APIKey.user_id == user_id
        ).first()
        
        if not api_key:
            return False
        
        api_key.is_default = True
        self.db.commit()
        return True
    
    async def toggle_provider(self, user_id: int, api_key_id: int) -> bool:
        """Toggle a provider's active status."""
        api_key = self.db.query(APIKey).filter(
            APIKey.id == api_key_id,
            APIKey.user_id == user_id
        ).first()
        
        if not api_key:
            return False
        
        api_key.is_active = not api_key.is_active
        self.db.commit()
        return True
    
    async def bulk_validate_user_api_keys(self, user_id: int) -> List[Dict]:
        """Concurrently validate all active API keys for a user."""
        user_keys = self.db.query(APIKey).filter(
            APIKey.user_id == user_id,
            APIKey.is_active == True
        ).all()

        if not user_keys:
            return []

        validation_tasks = [self.validate_api_key(key.id) for key in user_keys]
        await asyncio.gather(*validation_tasks)

        # Re-fetch the keys to get updated validation status
        self.db.expire_all()
        updated_keys = self.db.query(APIKey).filter(
            APIKey.id.in_([key.id for key in user_keys])
        ).all()

        results = []
        for key in updated_keys:
            results.append({
                "id": key.id,
                "provider": key.provider,
                "is_valid": key.is_valid,
                "error_message": key.validation_error
            })
        
        return results
    
    def get_provider_info(self) -> Dict:
        """Get information about all supported providers."""
        return self.SUPPORTED_PROVIDERS