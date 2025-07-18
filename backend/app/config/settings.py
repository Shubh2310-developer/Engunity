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
    supabase_url: str = "https://ckrtquhwlvpmpgrfemmb.supabase.co"
    supabase_anon_key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNrcnRxdWh3bHZwbXBncmZlbW1iIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk2NTE5MjQsImV4cCI6MjA2NTIyNzkyNH0.EKkuLjGdt3BJckM9XtboDCknG5ggt0xwcAI_jI8Al6k"
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
        "http://localhost:8080",  # Frontend test server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",  # Frontend test server
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
    ]
    
    # Frontend URLs
    frontend_url: str = "http://localhost:3000"
    
    # Session Configuration
    session_expire_minutes: int = 60 * 24  # 24 hours
    
    # Document Processing Configuration
    groq_model: str = "llama3-70b-8192"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 400
    chunk_overlap: int = 50
    max_concurrent_processing: int = 3
    
    # Vector Store Configuration
    vector_store_path: str = "./vector_store"
    
    # File Upload Configuration
    max_file_size: int = 10485760  # 10MB
    upload_path: str = "./uploads"
    allowed_extensions: str = ".pdf,.docx,.txt,.md"
    
    # S3/Supabase Storage Configuration
    s3_access_key_id: str = "daef80b0f4b050e45e7dedf3d993cf79"
    s3_secret_access_key: str = "13abac6ee7f8414dc561c8306ee24bf4d05e93d5082462c165a1299af53f72f9"
    s3_bucket_name: str = "documents"
    s3_region: str = "us-east-1"
    s3_endpoint_url: str = "https://ckrtquhwlvpmpgrfemmb.supabase.co/storage/v1/s3"
    
    # Pagination
    default_page_size: int = 10
    max_page_size: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        env_file_encoding = 'utf-8'
    
    def get_allowed_extensions(self) -> List[str]:
        """Get allowed extensions as a list."""
        return [ext.strip() for ext in self.allowed_extensions.split(',')]

# Create settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get settings instance."""
    return settings