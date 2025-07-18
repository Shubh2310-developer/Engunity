#!/usr/bin/env python3
"""
Test Supabase authentication to create a test user.
"""

import asyncio
from app.services.auth_service import SupabaseAuthService
from app.schemas.auth import UserRegister, UserLogin

async def test_auth():
    """Test Supabase authentication."""
    auth_service = SupabaseAuthService()
    
    # Test user data
    test_user = UserRegister(
        email="test@engunity.com",
        password="Test123!@#",
        full_name="Test User"
    )
    
    test_login = UserLogin(
        email="test@engunity.com", 
        password="Test123!@#"
    )
    
    try:
        print("🔍 Testing Supabase Authentication...")
        
        # Test 1: Register new user
        try:
            print(f"📝 Attempting to register user: {test_user.email}")
            register_result = await auth_service.register_user(test_user)
            print(f"✅ User registered successfully!")
            print(f"   User ID: {register_result['user'].id}")
            print(f"   Email: {register_result['user'].email}")
            if register_result['session']:
                print(f"   Access Token: {register_result['session'].access_token[:50]}...")
        except Exception as e:
            if "already registered" in str(e).lower():
                print(f"ℹ️  User already exists: {test_user.email}")
            else:
                print(f"❌ Registration failed: {e}")
        
        # Test 2: Login with user
        try:
            print(f"\n🔐 Attempting to login user: {test_login.email}")
            login_result = await auth_service.login_user(test_login)
            print(f"✅ User logged in successfully!")
            print(f"   User ID: {login_result['user'].id}")
            print(f"   Email: {login_result['user'].email}")
            print(f"   Access Token: {login_result['session'].access_token[:50]}...")
            
            # Test 3: Validate token
            access_token = login_result['session'].access_token
            print(f"\n🔍 Testing token validation...")
            user_from_token = await auth_service.get_user_by_token(access_token)
            if user_from_token:
                print(f"✅ Token validation successful!")
                print(f"   User ID from token: {user_from_token.id}")
                print(f"   Email from token: {user_from_token.email}")
            else:
                print(f"❌ Token validation failed")
                
            return access_token
            
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return None
        
    except Exception as e:
        print(f"❌ Auth test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    token = asyncio.run(test_auth())
    if token:
        print(f"\n🎉 Authentication test successful!")
        print(f"Test credentials:")
        print(f"  Email: test@engunity.com")
        print(f"  Password: Test123!@#")
        print(f"  Token: {token[:50]}...")
    else:
        print(f"\n❌ Authentication test failed")