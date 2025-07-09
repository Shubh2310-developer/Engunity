#!/usr/bin/env python3
"""Development server startup script."""

import sys
import os
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import and create database tables
from app.config.database import create_tables

def main():
    """Start the development server."""
    try:
        # Create database tables
        print("Creating database tables...")
        create_tables()
        print("Database tables created successfully.")
        
        # Start the server
        print("Starting development server...")
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()