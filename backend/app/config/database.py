"""Database configuration for both Supabase and local SQLAlchemy."""

import os
from supabase import create_client, Client
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .settings import settings

# Supabase configuration
supabase: Client = create_client(
    settings.supabase_url or "https://placeholder.supabase.co",
    settings.supabase_anon_key or "placeholder"
)

def get_supabase() -> Client:
    """Get Supabase client instance."""
    return supabase

# For admin operations (server-side only)
def get_supabase_admin() -> Client:
    """Get Supabase admin client for server-side operations."""
    return create_client(
        settings.supabase_url or "https://placeholder.supabase.co",
        settings.supabase_service_role_key or "placeholder"
    )

# SQLAlchemy configuration for local database
SQLALCHEMY_DATABASE_URL = "sqlite:///./engunity.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)