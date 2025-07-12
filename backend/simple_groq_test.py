#!/usr/bin/env python3
"""Simple Groq API test."""

import os
import httpx
import asyncio

async def test_groq_simple():
    """Test Groq API with simple HTTP request."""
    
    # Use the first fallback key
    api_key = "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"
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "user", "content": "Say hello in one word"}
        ],
        "max_tokens": 10,
        "temperature": 0.7
    }
    
    try:
        print("Testing Groq API...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=data, headers=headers)
            
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("choices"):
                content = result["choices"][0]["message"]["content"]
                print(f"AI Response: {content}")
            print("✅ Groq API is working!")
        else:
            print("❌ Groq API error")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_groq_simple())