"""Application settings and configuration."""

import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    
    # App Info
    app_name: str = "Engunity AI"
    version: str = "1.0.0"
    debug: bool = False
    
    # Supabase Configuration
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    
    # Database Configuration (for direct PostgreSQL access if needed)
    database_url: str = "sqlite:///./engunity.db"
    
    # MongoDB Configuration
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "Chats"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Groq Configuration
    groq_api_key: str = ""
    
    # Fallback Groq API Keys (for when users don't have their own keys)
    fallback_groq_keys: List[str] = [
        "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",
        "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",
        "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",
        "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",
        "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"
    ]
    
    # CORS
    allowed_hosts: List[str] = ["*"]
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
    ]
    
    # Frontend URLs
    frontend_url: str = "http://localhost:3000"
    
    # Session Configuration
    session_expire_minutes: int = 60 * 24  # 24 hours
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        env_file_encoding = 'utf-8'

# Create settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get settings instance."""
    return settings