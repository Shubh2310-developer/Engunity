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
    database_url: str = ""
    
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

# Create settings instance
settings = Settings()