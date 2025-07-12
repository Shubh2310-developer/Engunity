#!/usr/bin/env python3
"""Test script to verify Supabase and MongoDB connections."""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/home/ghost/engunity/backend/.env')

# Add the backend directory to the path
sys.path.insert(0, '/home/ghost/engunity/backend')

from app.config.database import get_supabase, mongo_manager
from app.services.auth_service import SupabaseAuthService
from app.db.repositories.mongo_repository import get_repository_manager
from app.models.mongo_models import ChatHistory, ChatMessage


async def test_supabase_connection():
    """Test Supabase connection and authentication."""
    print("🔍 Testing Supabase Connection...")
    
    try:
        # Get Supabase client
        supabase = get_supabase()
        print("✅ Supabase client created successfully")
        
        # Test auth service
        auth_service = SupabaseAuthService()
        print("✅ Auth service initialized")
        
        # Test a simple query (this will fail if connection is bad)
        try:
            # Try to get the current user (will return None if not authenticated)
            response = supabase.auth.get_session()
            print("✅ Supabase auth endpoint accessible")
        except Exception as e:
            print(f"⚠️  Supabase auth test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False


async def test_mongodb_connection():
    """Test MongoDB connection."""
    print("\n🔍 Testing MongoDB Connection...")
    
    try:
        # Connect to MongoDB
        await mongo_manager.connect()
        print("✅ MongoDB connection established")
        
        # Get database
        db = mongo_manager.get_database()
        if db is not None:
            print("✅ MongoDB database accessible")
            
            # Test basic operations
            collection = db.test_collection
            
            # Insert a test document
            test_doc = {
                "test": True,
                "timestamp": datetime.utcnow(),
                "message": "Connection test"
            }
            
            result = await collection.insert_one(test_doc)
            print(f"✅ Test document inserted with ID: {result.inserted_id}")
            
            # Find the document
            found_doc = await collection.find_one({"_id": result.inserted_id})
            if found_doc:
                print("✅ Test document retrieved successfully")
            
            # Clean up
            await collection.delete_one({"_id": result.inserted_id})
            print("✅ Test document cleaned up")
            
        else:
            print("❌ MongoDB database not accessible")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False
    
    finally:
        # Disconnect
        await mongo_manager.disconnect()


async def test_repository_manager():
    """Test MongoDB repository manager."""
    print("\n🔍 Testing Repository Manager...")
    
    try:
        # Get repository manager
        repo_manager = await get_repository_manager()
        print("✅ Repository manager initialized")
        
        # Test chat repository
        test_user_id = "test_user_123"
        chat_title = "Test Chat"
        
        # Create a test chat
        chat_id = await repo_manager.chat_repo.create_chat(test_user_id, chat_title)
        print(f"✅ Test chat created with ID: {chat_id}")
        
        # Add a test message
        test_message = ChatMessage(
            role="user",
            content="Hello, this is a test message!",
            message_type="text"
        )
        
        success = await repo_manager.chat_repo.add_message(chat_id, test_message)
        if success:
            print("✅ Test message added successfully")
        
        # Retrieve the chat
        chat = await repo_manager.chat_repo.get_chat_by_id(chat_id)
        if chat and len(chat.messages) > 0:
            print("✅ Test chat and message retrieved successfully")
            print(f"   Chat title: {chat.title}")
            print(f"   Messages: {len(chat.messages)}")
            print(f"   Last message: {chat.messages[-1].content}")
        
        # Clean up
        deleted = await repo_manager.chat_repo.delete_chat(chat_id, test_user_id)
        if deleted:
            print("✅ Test chat cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Repository manager test failed: {e}")
        return False


async def test_collections_structure():
    """Test MongoDB collections structure."""
    print("\n🔍 Testing Collections Structure...")
    
    try:
        await mongo_manager.connect()
        db = mongo_manager.get_database()
        
        # Check expected collections
        expected_collections = [
            "chat_history", "codes", "images", "pdfs", "user_stats"
        ]
        
        existing_collections = await db.list_collection_names()
        print(f"✅ Existing collections: {existing_collections}")
        
        # Create indexes for all collections
        repo_manager = await get_repository_manager()
        await repo_manager.create_all_indexes()
        print("✅ All indexes created successfully")
        
        # Test each collection
        for collection_name in expected_collections:
            collection = db[collection_name]
            indexes = await collection.list_indexes().to_list(length=None)
            print(f"✅ Collection '{collection_name}' has {len(indexes)} indexes")
        
        return True
        
    except Exception as e:
        print(f"❌ Collections structure test failed: {e}")
        return False
    
    finally:
        await mongo_manager.disconnect()


async def main():
    """Run all tests."""
    print("🧪 Testing Engunity Backend Connections\n")
    
    tests = [
        ("Supabase Connection", test_supabase_connection),
        ("MongoDB Connection", test_mongodb_connection),
        ("Repository Manager", test_repository_manager),
        ("Collections Structure", test_collections_structure)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"{'='*50}")
        print(f"Running {test_name} Test")
        print(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready.")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)