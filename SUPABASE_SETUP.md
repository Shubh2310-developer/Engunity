# 🚀 Supabase Authentication Setup Guide for Engunity AI

This guide will help you set up Supabase authentication for your Engunity AI application with user-specific content and complete session management.

## 📋 **Requirements**

### **1. Supabase Account Setup**
- Create a free account at [supabase.com](https://supabase.com)
- Create a new project in your Supabase dashboard
- Note down your project URL and API keys

### **2. Dependencies Installed**
```bash
# Backend dependencies
cd backend
pip install -r requirements/base.txt

# Key packages:
# - supabase==2.3.0
# - fastapi==0.104.1
# - uvicorn==0.24.0
```

### **3. Environment Variables**
Copy `.env.example` to `.env` and fill in your Supabase credentials:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# Application
DEBUG=true
APP_NAME=Engunity AI
VERSION=1.0.0
FRONTEND_URL=http://localhost:3000
SESSION_EXPIRE_MINUTES=1440

# CORS Origins
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000,http://localhost:5173,http://127.0.0.1:5173
```

## 🗄️ **Database Setup**

### **1. Enable Authentication in Supabase**
1. Go to your Supabase project dashboard
2. Navigate to **Authentication** → **Settings**
3. Enable **Email Authentication**
4. Configure **Site URL**: `http://localhost:3000`
5. Add **Redirect URLs**: `http://localhost:3000/dashboard.html`

### **2. Create User Profiles Table**
Run this SQL in your Supabase SQL editor:

```sql
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
```

### **3. Create User Content Tables**
```sql
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
```

## 🔧 **Frontend Configuration**

### **1. Update Supabase Service Configuration**
Edit `/frontend/scripts/services/supabase-service.js`:

```javascript
constructor() {
    // Replace with your actual Supabase credentials
    this.supabaseUrl = 'https://your-project-id.supabase.co';
    this.supabaseAnonKey = 'your-supabase-anon-key';
    
    // Initialize Supabase client
    this.supabase = window.supabase?.createClient(this.supabaseUrl, this.supabaseAnonKey);
}
```

### **2. Updated HTML Pages**
All HTML pages now include:
- ✅ **Supabase CDN script**
- ✅ **Supabase service integration**
- ✅ **Automatic session management**
- ✅ **User-specific routing**

## 🚀 **Running the Application**

### **1. Start the Backend**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **2. Serve the Frontend**
```bash
cd frontend
# Using Python
python -m http.server 3000

# Or using Node.js
npx serve public -p 3000
```

### **3. Test Authentication**
1. Open `http://localhost:3000`
2. Navigate to **Register** to create an account
3. Check your email for verification (if enabled)
4. Login with your credentials
5. Access the dashboard with user-specific content

## 🔐 **Authentication Flow**

### **Registration Process**
1. User fills registration form
2. Supabase creates user account
3. Automatic profile creation via trigger
4. Email verification sent (optional)
5. User redirected to dashboard

### **Login Process**
1. User enters credentials
2. Supabase validates and creates session
3. Access token stored automatically
4. User redirected to dashboard
5. Dashboard loads user-specific content

### **User-Specific Content**
- ✅ **Automatic user isolation** via Row Level Security
- ✅ **User projects, documents, and chats**
- ✅ **Profile management**
- ✅ **Session persistence**

## 🔗 **API Endpoints**

Your backend now provides these Supabase-powered endpoints:

```
POST /api/v1/auth/register      - Register new user
POST /api/v1/auth/login         - Login user
POST /api/v1/auth/logout        - Logout user
POST /api/v1/auth/forgot-password - Request password reset
POST /api/v1/auth/reset-password  - Reset password
POST /api/v1/auth/refresh       - Refresh access token
GET  /api/v1/auth/me           - Get current user
GET  /api/v1/auth/profile/{id} - Get user profile
PUT  /api/v1/auth/profile      - Update user profile
```

## 🛡️ **Security Features**

- ✅ **Row Level Security (RLS)** - Users can only access their own data
- ✅ **JWT Token Authentication** - Secure session management
- ✅ **Automatic token refresh** - Seamless user experience
- ✅ **Email verification** - Optional security layer
- ✅ **Password reset** - Secure password recovery

## 🎯 **User Experience Features**

- ✅ **Persistent sessions** - Users stay logged in
- ✅ **Automatic redirects** - Smart routing based on auth state
- ✅ **Loading animations** - Beautiful AI Orbital Loader
- ✅ **Error handling** - User-friendly error messages
- ✅ **Real-time validation** - Instant form feedback

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Supabase not connecting**
   - Check your URL and API keys
   - Verify CORS settings in Supabase dashboard
   - Check browser console for errors

2. **Users can't register**
   - Verify email authentication is enabled
   - Check if email confirmation is required
   - Review authentication settings

3. **Dashboard not loading user data**
   - Verify RLS policies are created
   - Check if user profile was created
   - Confirm user is authenticated

4. **CORS errors**
   - Add your domain to CORS_ORIGINS in .env
   - Update Supabase CORS settings

## 📞 **Support**

If you encounter issues:
1. Check the browser console for errors
2. Review Supabase dashboard logs
3. Verify all environment variables are set
4. Ensure database tables and policies exist

Your authentication system is now fully integrated with Supabase and provides complete user management with isolated, secure content for each user! 🎉