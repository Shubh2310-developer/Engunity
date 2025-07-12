#!/usr/bin/env python3
"""Test the Groq API keys to ensure they work."""

import asyncio
from groq import Groq

# Test API keys
test_keys = [
    "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",
    "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",
    "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",
    "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",
    "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"
]

async def test_groq_key(api_key: str) -> bool:
    """Test a single Groq API key."""
    try:
        client = Groq(api_key=api_key)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Hello! Please respond with 'Working' if you can read this."}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        print(f"Key {api_key[-8:]}: ✅ Working - Response: {result}")
        return True
        
    except Exception as e:
        print(f"Key {api_key[-8:]}: ❌ Failed - Error: {str(e)}")
        return False

async def test_all_keys():
    """Test all provided API keys."""
    print("Testing Groq API keys...\n")
    
    working_keys = []
    
    for i, key in enumerate(test_keys, 1):
        print(f"Testing key {i}/5...")
        is_working = await test_groq_key(key)
        if is_working:
            working_keys.append(key)
        print()
    
    print(f"Summary: {len(working_keys)}/{len(test_keys)} keys are working")
    
    if working_keys:
        print(f"\nWorking keys:")
        for key in working_keys:
            print(f"  - {key}")
    else:
        print("\n❌ No working keys found!")

if __name__ == "__main__":
    asyncio.run(test_all_keys())