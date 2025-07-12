#!/usr/bin/env python3
"""Test Groq service directly."""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.groq_service import create_groq_completion

async def test_groq():
    """Test Groq service directly."""
    try:
        print("Testing Groq service...")
        
        messages = [
            {"role": "user", "content": "Hello, can you say hi back?"}
        ]
        
        response = await create_groq_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=100
        )
        
        print("Success! Response:")
        print(response)
        
        if response.get("choices") and len(response["choices"]) > 0:
            content = response["choices"][0]["message"]["content"]
            print(f"\nAI Response: {content}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_groq())