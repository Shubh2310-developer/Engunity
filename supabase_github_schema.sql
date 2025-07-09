-- GitHub Integration Schema for Supabase
-- This file contains the SQL schema for GitHub integration features

-- Add GitHub-specific columns to profiles table
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS github_id TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS github_username TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS github_email TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS github_avatar_url TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS github_connected_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;

-- Create index for GitHub lookups
CREATE INDEX IF NOT EXISTS idx_profiles_github_id ON profiles(github_id);
CREATE INDEX IF NOT EXISTS idx_profiles_github_username ON profiles(github_username);

-- Update user_projects table to support GitHub repository data
ALTER TABLE user_projects ADD COLUMN IF NOT EXISTS project_type TEXT DEFAULT 'manual';
ALTER TABLE user_projects ADD COLUMN IF NOT EXISTS project_data JSONB DEFAULT '{}';

-- Add GitHub-specific project types
ALTER TABLE user_projects ADD CONSTRAINT check_project_type 
    CHECK (project_type IN ('manual', 'github_import', 'github_clone', 'github_fork'));

-- Update RLS policies for profiles to include GitHub data
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
DROP POLICY IF EXISTS "Users can insert own profile" ON profiles;

-- Recreate RLS policies with GitHub support
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

-- Update RLS policies for user_projects to support GitHub projects
DROP POLICY IF EXISTS "Users can view own projects" ON user_projects;
DROP POLICY IF EXISTS "Users can manage own projects" ON user_projects;

-- Recreate RLS policies for user_projects
CREATE POLICY "Users can view own projects" ON user_projects
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own projects" ON user_projects
    FOR ALL USING (auth.uid() = user_id);

-- Function to handle GitHub account linking
CREATE OR REPLACE FUNCTION handle_github_linking()
RETURNS TRIGGER AS $$
BEGIN
    -- Update profile with GitHub data if user signs in with GitHub
    IF NEW.provider = 'github' THEN
        UPDATE profiles 
        SET 
            github_id = NEW.identity_data->>'sub',
            github_username = NEW.identity_data->>'user_name',
            github_email = NEW.identity_data->>'email',
            github_avatar_url = NEW.identity_data->>'avatar_url',
            github_connected_at = NOW(),
            email_verified = CASE 
                WHEN NEW.identity_data->>'email' = (SELECT email FROM auth.users WHERE id = NEW.user_id) 
                THEN TRUE 
                ELSE email_verified 
            END
        WHERE id = NEW.user_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for GitHub account linking
DROP TRIGGER IF EXISTS trigger_github_linking ON auth.identities;
CREATE TRIGGER trigger_github_linking
    AFTER INSERT ON auth.identities
    FOR EACH ROW
    EXECUTE FUNCTION handle_github_linking();

-- Create function to merge users with same email
CREATE OR REPLACE FUNCTION merge_users_by_email()
RETURNS TRIGGER AS $$
DECLARE
    existing_user_id UUID;
    github_data JSONB;
BEGIN
    -- Check if there's already a user with this email
    SELECT id INTO existing_user_id
    FROM auth.users 
    WHERE email = NEW.identity_data->>'email'
    AND id != NEW.user_id;
    
    -- If found, update the existing user's profile with GitHub data
    IF existing_user_id IS NOT NULL THEN
        UPDATE profiles 
        SET 
            github_id = NEW.identity_data->>'sub',
            github_username = NEW.identity_data->>'user_name',
            github_email = NEW.identity_data->>'email',
            github_avatar_url = NEW.identity_data->>'avatar_url',
            github_connected_at = NOW(),
            email_verified = TRUE
        WHERE id = existing_user_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for email-based user merging
DROP TRIGGER IF EXISTS trigger_merge_users_by_email ON auth.identities;
CREATE TRIGGER trigger_merge_users_by_email
    AFTER INSERT ON auth.identities
    FOR EACH ROW
    WHEN (NEW.provider = 'github')
    EXECUTE FUNCTION merge_users_by_email();

-- Create view for GitHub-enabled users
CREATE OR REPLACE VIEW github_users AS
SELECT 
    p.id,
    p.full_name,
    p.github_id,
    p.github_username,
    p.github_email,
    p.github_avatar_url,
    p.github_connected_at,
    p.email_verified,
    u.email,
    u.created_at as user_created_at
FROM profiles p
JOIN auth.users u ON p.id = u.id
WHERE p.github_id IS NOT NULL;

-- Grant access to the view
GRANT SELECT ON github_users TO authenticated;

-- Create view for GitHub projects
CREATE OR REPLACE VIEW github_projects AS
SELECT 
    up.id,
    up.user_id,
    up.name,
    up.description,
    up.project_type,
    up.project_data,
    up.created_at,
    up.updated_at,
    p.github_username
FROM user_projects up
JOIN profiles p ON up.user_id = p.id
WHERE up.project_type LIKE 'github_%';

-- Grant access to the view
GRANT SELECT ON github_projects TO authenticated;

-- Create function to get user's GitHub repositories
CREATE OR REPLACE FUNCTION get_user_github_repos(user_uuid UUID)
RETURNS TABLE (
    repo_id TEXT,
    repo_name TEXT,
    repo_url TEXT,
    description TEXT,
    language TEXT,
    stars INTEGER,
    forks INTEGER,
    imported_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (project_data->>'repo_id')::TEXT as repo_id,
        (project_data->>'repo_name')::TEXT as repo_name,
        (project_data->>'repo_url')::TEXT as repo_url,
        (project_data->>'description')::TEXT as description,
        (project_data->>'language')::TEXT as language,
        (project_data->>'stars')::INTEGER as stars,
        (project_data->>'forks')::INTEGER as forks,
        (project_data->>'imported_at')::TIMESTAMP WITH TIME ZONE as imported_at
    FROM user_projects 
    WHERE user_id = user_uuid 
    AND project_type = 'github_import'
    ORDER BY created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION get_user_github_repos(UUID) TO authenticated;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_projects_type ON user_projects(project_type);
CREATE INDEX IF NOT EXISTS idx_user_projects_user_id ON user_projects(user_id);
CREATE INDEX IF NOT EXISTS idx_user_projects_created_at ON user_projects(created_at);

-- Create index on JSONB project_data for GitHub repo lookups
CREATE INDEX IF NOT EXISTS idx_user_projects_repo_id ON user_projects USING GIN ((project_data->>'repo_id'));
CREATE INDEX IF NOT EXISTS idx_user_projects_repo_name ON user_projects USING GIN ((project_data->>'repo_name'));

-- Insert some sample project types for reference
INSERT INTO user_projects (id, user_id, name, description, project_type, project_data, created_at)
VALUES 
    ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000000', 'Sample Manual Project', 'A manually created project', 'manual', '{}', NOW()),
    ('00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000000', 'Sample GitHub Import', 'A GitHub repository import', 'github_import', '{"repo_id": "123456789", "repo_name": "sample-repo", "repo_url": "https://github.com/user/sample-repo", "description": "Sample repository", "language": "JavaScript", "stars": 42, "forks": 7, "imported_at": "2024-01-01T00:00:00Z"}', NOW())
ON CONFLICT (id) DO NOTHING;

-- Create function to handle OAuth user creation
CREATE OR REPLACE FUNCTION handle_oauth_user_creation()
RETURNS TRIGGER AS $$
BEGIN
    -- Create profile for OAuth users
    INSERT INTO profiles (id, full_name, avatar_url, created_at, updated_at)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
        NEW.raw_user_meta_data->>'avatar_url',
        NOW(),
        NOW()
    )
    ON CONFLICT (id) DO UPDATE SET
        full_name = COALESCE(EXCLUDED.full_name, profiles.full_name),
        avatar_url = COALESCE(EXCLUDED.avatar_url, profiles.avatar_url),
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for OAuth user profile creation
DROP TRIGGER IF EXISTS trigger_oauth_user_creation ON auth.users;
CREATE TRIGGER trigger_oauth_user_creation
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_oauth_user_creation();

-- Comments for documentation
COMMENT ON TABLE profiles IS 'Extended user profile information with GitHub integration support';
COMMENT ON COLUMN profiles.github_id IS 'GitHub user ID from OAuth provider';
COMMENT ON COLUMN profiles.github_username IS 'GitHub username from OAuth provider';
COMMENT ON COLUMN profiles.github_email IS 'GitHub email from OAuth provider';
COMMENT ON COLUMN profiles.github_avatar_url IS 'GitHub avatar URL from OAuth provider';
COMMENT ON COLUMN profiles.github_connected_at IS 'Timestamp when GitHub account was connected';
COMMENT ON COLUMN profiles.email_verified IS 'Whether the email has been verified through GitHub OAuth';

COMMENT ON TABLE user_projects IS 'User projects with support for GitHub repository imports';
COMMENT ON COLUMN user_projects.project_type IS 'Type of project: manual, github_import, github_clone, github_fork';
COMMENT ON COLUMN user_projects.project_data IS 'JSON data containing project-specific information, including GitHub repository data';

COMMENT ON FUNCTION get_user_github_repos(UUID) IS 'Retrieves all GitHub repositories imported by a specific user';
COMMENT ON FUNCTION handle_github_linking() IS 'Handles linking of GitHub accounts to existing user profiles';
COMMENT ON FUNCTION merge_users_by_email() IS 'Merges GitHub OAuth users with existing users based on email address';
COMMENT ON FUNCTION handle_oauth_user_creation() IS 'Creates profile entries for OAuth users including GitHub users';