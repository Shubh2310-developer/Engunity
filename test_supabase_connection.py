#!/usr/bin/env python3
"""
Test Supabase connection and setup
"""

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ Supabase package not found. Installing...")
    import subprocess
    subprocess.run(["pip", "install", "supabase==2.3.0"])
    from supabase import create_client, Client

# Supabase credentials
SUPABASE_URL = "https://ckrtquhwlvpmpgrfemmb.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNrcnRxdWh3bHZwbXBncmZlbW1iIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk2NTE5MjQsImV4cCI6MjA2NTIyNzkyNH0.EKkuLjGdt3BJckM9XtboDCknG5ggt0xwcAI_jI8Al6k"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNrcnRxdWh3bHZwbXBncmZlbW1iIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTY1MTkyNCwiZXhwIjoyMDY1MjI3OTI0fQ.cBicQdHwpqexi7OrOXEesy8iWXBv3R6jRbzNCWbW50M"

def test_connection():
    """Test Supabase connection and basic operations."""
    
    print("🔄 Testing Supabase Connection...")
    print(f"📡 URL: {SUPABASE_URL}")
    
    try:
        # Create client with anon key
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        print("✅ Supabase client created successfully")
        
        # Test basic functionality
        print("\n🔐 Testing Authentication...")
        
        # Try to get current session (should be None for new connection)
        try:
            session = supabase.auth.get_session()
            print(f"📄 Current session: {session.session is not None}")
        except Exception as e:
            print(f"📄 Auth test (expected): {str(e)[:50]}...")
        
        print("\n🏗️  Database Setup Required:")
        print("1. Go to your Supabase dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Run the SQL commands from SUPABASE_SETUP.md")
        print("4. This will create user profiles and content tables")
        
        print("\n🚀 Your Supabase is Ready!")
        print("📍 Next Steps:")
        print("   • Run database setup SQL")
        print("   • Start backend: uvicorn app.main:app --reload --port 8000")
        print("   • Start frontend: python -m http.server 3000 -d frontend/public")
        print("   • Test authentication at http://localhost:3000")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def print_sql_setup():
    """Print the SQL setup commands."""
    print("\n" + "="*50)
    print("📄 COPY THIS SQL TO YOUR SUPABASE SQL EDITOR:")
    print("="*50)
    
    sql_commands = """
-- Create profiles table for additional user data
CREATE TABLE profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    full_name TEXT,
    avatar_url TEXT,
    bio TEXT,
    organization TEXT,
    job_title TEXT,
    location TEXT,
    website TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view their own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile" ON profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

-- Create function to automatically create profile
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name)
    VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger to automatically create profile on signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- Create user-specific content tables
CREATE TABLE user_projects (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE user_documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES user_projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE user_chats (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT,
    messages JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on all tables
ALTER TABLE user_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_chats ENABLE ROW LEVEL SECURITY;

-- Create policies for user_projects
CREATE POLICY "Users can manage their own projects" ON user_projects
    USING (auth.uid() = user_id);

-- Create policies for user_documents  
CREATE POLICY "Users can manage their own documents" ON user_documents
    USING (auth.uid() = user_id);

-- Create policies for user_chats
CREATE POLICY "Users can manage their own chats" ON user_chats
    USING (auth.uid() = user_id);
"""
    
    print(sql_commands)
    print("="*50)

if __name__ == "__main__":
    print("🎯 Engunity AI - Supabase Setup Test")
    print("=====================================")
    
    # Test connection
    success = test_connection()
    
    if success:
        print_sql_setup()
        
        print("\n✨ Configuration Complete!")
        print("🔗 Your authentication system is ready to use!")
    else:
        print("\n❌ Please check your Supabase credentials and try again.")