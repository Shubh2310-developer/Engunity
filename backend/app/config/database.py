"""Database configuration for Supabase, MongoDB, and local SQLAlchemy."""

import os
from typing import Optional
from supabase import create_client, Client
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
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

# MongoDB configuration
class MongoManager:
    """MongoDB connection manager."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        
    async def connect(self):
        """Connect to MongoDB."""
        if not self.client:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.database = self.client[settings.mongodb_database]
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            self.client = None
            self.database = None
    
    def get_database(self):
        """Get MongoDB database instance."""
        return self.database
    
    def get_collection(self, collection_name: str):
        """Get MongoDB collection."""
        if self.database:
            return self.database[collection_name]
        return None

# Global MongoDB manager instance
mongo_manager = MongoManager()

async def get_mongo_db():
    """Get MongoDB database dependency."""
    await mongo_manager.connect()
    return mongo_manager.get_database()

def get_mongo_collection(collection_name: str):
    """Get MongoDB collection dependency."""
    return mongo_manager.get_collection(collection_name)