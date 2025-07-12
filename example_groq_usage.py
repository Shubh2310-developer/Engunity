#!/usr/bin/env python3
"""Example of how to use the Groq llama-3.3-70b-versatile integration."""

import asyncio
import json
from groq import Groq

def example_direct_groq_usage():
    """Example using Groq directly as specified."""
    
    # Your exact code specification
    client = Groq()
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": "Explain quantum computing in simple terms"
            }
        ],
        temperature=1,
        max_completion_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )

    print("🔥 Direct Groq API Response (Streaming):")
    for chunk in completion:
        content = chunk.choices[0].delta.content or ""
        if content:
            print(content, end="")
    print("\n")

async def example_backend_integration():
    """Example using the backend service."""
    import sys
    sys.path.insert(0, '/home/ghost/engunity/backend')
    
    from app.services.groq_service import create_groq_completion, create_groq_stream
    
    messages = [
        {
            "role": "user", 
            "content": "Write a short Python function to calculate fibonacci numbers"
        }
    ]
    
    print("🚀 Backend Service Response (Non-streaming):")
    try:
        # Non-streaming completion
        completion = await create_groq_completion(
            messages=messages,
            temperature=1.0,
            max_tokens=1024,
            top_p=1.0,
            stream=False
        )
        
        response = completion['choices'][0]['message']['content']
        print(response)
        print(f"\nModel used: {completion.get('model', 'unknown')}")
        print(f"Total tokens: {completion.get('usage', {}).get('total_tokens', 'unknown')}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Note: This requires a valid GROQ_API_KEY in environment")

async def example_streaming_backend():
    """Example using backend streaming."""
    import sys
    sys.path.insert(0, '/home/ghost/engunity/backend')
    
    from app.services.groq_service import create_groq_stream
    
    messages = [
        {
            "role": "user", 
            "content": "Tell me a short story about AI and humans working together"
        }
    ]
    
    print("\n🌊 Backend Service Response (Streaming):")
    try:
        async for chunk in create_groq_stream(
            messages=messages,
            temperature=1.0,
            max_tokens=512,
            top_p=1.0
        ):
            if chunk.get("choices") and len(chunk["choices"]) > 0:
                delta = chunk["choices"][0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    print(content, end="")
        print("\n")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Note: This requires a valid GROQ_API_KEY in environment")

def example_api_request():
    """Example of making API request to backend."""
    print("\n📡 API Request Example:")
    
    api_request = {
        "url": "http://localhost:8001/api/v1/ai/chat/completions",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer YOUR_SUPABASE_JWT_TOKEN"
        },
        "body": {
            "messages": [
                {
                    "role": "user",
                    "content": "Explain the benefits of renewable energy"
                }
            ],
            "temperature": 1.0,
            "max_tokens": 1024,
            "top_p": 1.0,
            "stream": False,
            "save_conversation": True,
            "chat_id": "optional-chat-id-for-saving"
        }
    }
    
    print("curl command:")
    print(f"""
curl -X POST {api_request['url']} \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_SUPABASE_JWT_TOKEN" \\
  -d '{json.dumps(api_request['body'], indent=2)}'
""")

def main():
    """Run examples."""
    print("🎯 Groq llama-3.3-70b-versatile Integration Examples\n")
    
    print("="*60)
    print("1. DIRECT GROQ API USAGE (Your Specification)")
    print("="*60)
    
    # Only run if API key is available
    try:
        import os
        if os.getenv("GROQ_API_KEY") and os.getenv("GROQ_API_KEY") != "your-groq-api-key-here":
            example_direct_groq_usage()
        else:
            print("⚠️  GROQ_API_KEY not set. Skipping direct API example.")
            print("   Set GROQ_API_KEY environment variable to test.")
    except Exception as e:
        print(f"Direct API example failed: {e}")
    
    print("\n" + "="*60)
    print("2. BACKEND SERVICE INTEGRATION")
    print("="*60)
    
    # Run backend examples
    asyncio.run(example_backend_integration())
    asyncio.run(example_streaming_backend())
    
    print("\n" + "="*60)
    print("3. API REQUEST EXAMPLE")
    print("="*60)
    
    example_api_request()
    
    print("\n" + "="*60)
    print("INTEGRATION SUMMARY")
    print("="*60)
    
    print("""
✅ Model: llama-3.3-70b-versatile
✅ Provider: Groq  
✅ Temperature: 1.0
✅ Max Tokens: 1024
✅ Top P: 1.0
✅ Streaming: Supported
✅ Authentication: Supabase JWT
✅ Database: MongoDB for chat history
✅ API Endpoint: /api/v1/ai/chat/completions

🔧 Setup Required:
1. Set GROQ_API_KEY environment variable
2. Configure Supabase authentication  
3. Ensure MongoDB is running
4. Get JWT token from Supabase login

🚀 Ready to use!
""")

if __name__ == "__main__":
    main()