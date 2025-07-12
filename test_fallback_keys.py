#!/usr/bin/env python3
"""Test script for fallback API key functionality."""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.groq_service import GroqService, create_groq_completion


async def test_fallback_keys():
    """Test the fallback API key system."""
    print("Testing fallback API key system...")
    
    # Test 1: Service initialization with fallback keys
    print("\n1. Testing service initialization with fallback keys...")
    try:
        service = GroqService()
        print(f"✓ Service initialized successfully with key: {service.api_key[:20]}...")
    except Exception as e:
        print(f"✗ Service initialization failed: {e}")
        return False
    
    # Test 2: Simple chat completion
    print("\n2. Testing simple chat completion...")
    try:
        test_messages = [
            {"role": "user", "content": "Hello, can you respond with just 'Hi there!'?"}
        ]
        
        completion = await create_groq_completion(
            messages=test_messages,
            max_tokens=50,
            temperature=0.1
        )
        
        if completion and completion.get("choices"):
            response = completion["choices"][0]["message"]["content"]
            print(f"✓ Chat completion successful: {response}")
        else:
            print("✗ Chat completion failed: No response")
            return False
            
    except Exception as e:
        print(f"✗ Chat completion failed: {e}")
        return False
    
    # Test 3: API key validation
    print("\n3. Testing API key validation...")
    try:
        is_valid = await service.validate_api_key()
        if is_valid:
            print("✓ API key validation successful")
        else:
            print("✗ API key validation failed")
            return False
    except Exception as e:
        print(f"✗ API key validation error: {e}")
        return False
    
    # Test 4: Model info
    print("\n4. Testing model information...")
    try:
        models = service.get_available_models()
        model_info = service.get_model_info()
        print(f"✓ Available models: {len(models)} models")
        print(f"✓ Current model: {model_info.get('model', 'unknown')}")
    except Exception as e:
        print(f"✗ Model info error: {e}")
        return False
    
    print("\n✓ All tests passed! Fallback API key system is working correctly.")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_fallback_keys())
    sys.exit(0 if success else 1)