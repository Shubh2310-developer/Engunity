#!/usr/bin/env python3
"""Database setup script for Engunity AI."""

import asyncio
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine
from app.config.database import Base
from app.models.user import User  # Import all models

async def create_database():
    """Create the database if it doesn't exist."""
    # Connect to PostgreSQL without specifying database
    conn = await asyncpg.connect(
        user="engunity",
        password="password", 
        host="localhost",
        port=5432,
        database="postgres"  # Default database
    )
    
    try:
        # Check if database exists
        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'engunity_db'"
        )
        
        if not result:
            # Create database
            await conn.execute("CREATE DATABASE engunity_db")
            print("✅ Database 'engunity_db' created successfully")
        else:
            print("✅ Database 'engunity_db' already exists")
            
    except Exception as e:
        print(f"❌ Error creating database: {e}")
    finally:
        await conn.close()

async def create_tables():
    """Create all tables."""
    DATABASE_URL = "postgresql+asyncpg://engunity:password@localhost:5432/engunity_db"
    
    engine = create_async_engine(DATABASE_URL)
    
    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        print("✅ All tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
    finally:
        await engine.dispose()

async def main():
    """Main setup function."""
    print("🚀 Setting up Engunity AI Database...")
    
    # Create database
    await create_database()
    
    # Create tables
    await create_tables()
    
    print("\n✅ Database setup completed!")
    print("\nNext steps:")
    print("1. Copy .env.example to .env and update the values")
    print("2. Install dependencies: pip install -r requirements/base.txt")
    print("3. Run the application: uvicorn app.main:app --reload")

if __name__ == "__main__":
    asyncio.run(main())