#!/usr/bin/env python3
"""
Simple test script for Document Q&A system components
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_groq_service():
    """Test only the Groq service"""
    print("🧪 Testing Groq Service...")
    
    try:
        from app.services.groq_service import get_groq_service
        
        groq_service = get_groq_service()
        
        # Test simple completion
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is machine learning? Please answer in one sentence."}
        ]
        
        response = await groq_service.create_chat_completion(
            messages=messages,
            temperature=0.1,
            max_tokens=100
        )
        
        answer = response['choices'][0]['message']['content']
        print(f"✅ Groq completion successful: '{answer}'")
        
        # Test model info
        model_info = groq_service.get_model_info()
        print(f"✅ Model info: {model_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Groq service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_document_qa_api():
    """Test Document Q&A API structure"""
    print("\n🧪 Testing Document Q&A API Structure...")
    
    try:
        from app.api.v1.document_qa import router
        print(f"✅ Document Q&A router imported successfully")
        
        # Check if routes exist
        routes = [route.path for route in router.routes]
        print(f"✅ Available routes: {routes}")
        
        from app.services.document_qa_service import DocumentQAService
        print(f"✅ DocumentQAService imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Document Q&A API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_mongo_models():
    """Test MongoDB models"""
    print("\n🧪 Testing MongoDB Models...")
    
    try:
        from app.models.mongo_models import DocumentQAModel, DocumentChunkModel, DocumentQAInteractionModel
        
        # Test creating a document model
        doc_data = {
            "user_id": "test_user",
            "filename": "test.pdf",
            "title": "Test Document",
            "file_path": "/test/path",
            "file_type": "application/pdf",
            "file_size": 1024
        }
        
        doc = DocumentQAModel(**doc_data)
        print(f"✅ DocumentQAModel created: {doc.title}")
        
        # Test creating a chunk model
        chunk_data = {
            "document_id": "test_doc_id",
            "chunk_index": 0,
            "content": "This is a test chunk",
            "token_count": 5
        }
        
        chunk = DocumentChunkModel(**chunk_data)
        print(f"✅ DocumentChunkModel created: {chunk.content[:30]}...")
        
        # Test creating an interaction model
        interaction_data = {
            "document_id": "test_doc_id",
            "user_id": "test_user",
            "question": "What is this about?",
            "answer": "This is a test document"
        }
        
        interaction = DocumentQAInteractionModel(**interaction_data)
        print(f"✅ DocumentQAInteractionModel created: {interaction.question}")
        
        return True
        
    except Exception as e:
        print(f"❌ MongoDB models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_basic_imports():
    """Test basic imports"""
    print("\n🧪 Testing Basic Imports...")
    
    try:
        from app.config.settings import settings
        print(f"✅ Settings loaded: {settings.app_name}")
        
        from app.core.exceptions import DocumentQAError
        print(f"✅ DocumentQAError imported")
        
        from app.db.repositories.mongo_repository import DocumentQARepository
        print(f"✅ DocumentQARepository imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic imports test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Simple Document Q&A Tests\n")
    
    # Test individual components
    tests = [
        ("Basic Imports", test_basic_imports),
        ("MongoDB Models", test_mongo_models),
        ("Document Q&A API", test_document_qa_api),
        ("Groq Service", test_groq_service)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*50)
    print("🎯 TEST SUMMARY")
    print("="*50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Document Q&A system basic structure is working.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    # Set up environment
    os.environ.setdefault("GROQ_API_KEY", "")  # Will use fallback keys
    
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)