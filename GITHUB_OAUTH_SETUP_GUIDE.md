# GitHub OAuth Setup Guide

## Issue Identified
The GitHub OAuth is configured in the frontend but not properly set up in Supabase, causing a 404 error when users try to authenticate.

## Current Status
- ✅ Frontend code is configured for GitHub OAuth
- ❌ Supabase GitHub provider is not configured
- ❌ GitHub OAuth app is not created

## Step-by-Step Setup Instructions

### 1. Create GitHub OAuth App

1. **Go to GitHub Settings**:
   - Navigate to https://github.com/settings/developers
   - Click "OAuth Apps" → "New OAuth App"

2. **Configure OAuth App**:
   ```
   Application name: Engunity AI
   Homepage URL: https://your-domain.com
   Authorization callback URL: https://ckrtquhwlvpmpgrfemmb.supabase.co/auth/v1/callback
   ```

3. **Save Credentials**:
   - Copy the **Client ID**
   - Generate and copy the **Client Secret**

### 2. Configure Supabase GitHub Provider

1. **Go to Supabase Dashboard**:
   - Navigate to https://supabase.com/dashboard
   - Select your project: `ckrtquhwlvpmpgrfemmb`

2. **Enable GitHub Provider**:
   - Go to **Authentication** → **Providers**
   - Find **GitHub** and toggle it **ON**

3. **Add GitHub Credentials**:
   ```
   Client ID: [paste from GitHub OAuth app]
   Client Secret: [paste from GitHub OAuth app]
   ```

4. **Configure Redirect URLs**:
   - Add your domain redirect URLs:
   ```
   http://localhost:3000/pages/github-integration.html
   http://localhost:8000/pages/github-integration.html
   https://your-domain.com/pages/github-integration.html
   ```

### 3. Update Site URL in Supabase

1. **Go to Settings** → **General**
2. **Update Site URL**:
   ```
   Site URL: https://your-domain.com
   ```

### 4. Test the Configuration

1. **Test OAuth Flow**:
   - Go to your GitHub integration page
   - Click "Sign in with GitHub"
   - Should redirect to GitHub (not show 404)
   - After authorization, should return to your app

2. **Verify in Supabase**:
   - Check **Authentication** → **Users** for GitHub users
   - Verify identity data is populated

## For Development/Testing

### Local Development Setup

1. **Add localhost to GitHub OAuth**:
   ```
   Authorization callback URL: 
   - https://ckrtquhwlvpmpgrfemmb.supabase.co/auth/v1/callback
   - http://localhost:3000/pages/github-integration.html
   ```

2. **Update Supabase redirect URLs**:
   ```
   Additional redirect URLs:
   - http://localhost:3000/*
   - http://localhost:8000/*
   - http://127.0.0.1:*
   ```

### Testing Without GitHub OAuth

If you want to test the integration without setting up GitHub OAuth:

1. **Use Mock Data**:
   ```javascript
   // Add this to github-integration.html for testing
   function mockGitHubLogin() {
       localStorage.setItem('github_token', 'mock_token');
       localStorage.setItem('github_user', JSON.stringify({
           login: 'testuser',
           email: 'test@example.com',
           avatar_url: 'https://github.com/identicons/testuser.png',
           id: '12345',
           name: 'Test User'
       }));
       window.location.reload();
   }
   ```

2. **Add Test Button** (temporary):
   ```html
   <button onclick="mockGitHubLogin()" style="background: #28a745; color: white; padding: 10px; border: none; border-radius: 5px; margin: 10px;">
       Mock GitHub Login (Test Only)
   </button>
   ```

## Required GitHub OAuth Scopes

The application requests these scopes:
- `user:email` - Access user email addresses
- `repo` - Access public and private repositories

## Security Considerations

1. **Client Secret Security**:
   - Never expose client secret in frontend code
   - Only configure in Supabase dashboard (server-side)

2. **Redirect URI Validation**:
   - Only add trusted domains to redirect URIs
   - Use HTTPS in production

3. **Scope Minimization**:
   - Only request necessary scopes
   - Current scopes are appropriate for the functionality

## Troubleshooting

### Common Issues

1. **404 Error on GitHub OAuth**:
   - Check if GitHub OAuth app exists
   - Verify client ID in Supabase matches GitHub app
   - Ensure callback URL matches exactly

2. **Provider Not Found Error**:
   - GitHub provider not enabled in Supabase
   - Check Authentication → Providers → GitHub

3. **Redirect URI Mismatch**:
   - Callback URL in GitHub app doesn't match Supabase
   - Should be: `https://ckrtquhwlvpmpgrfemmb.supabase.co/auth/v1/callback`

4. **Invalid Client Error**:
   - Client ID or secret incorrect
   - Check credentials in both GitHub and Supabase

### Error Messages Reference

- `Provider not found` → Enable GitHub in Supabase
- `Invalid client` → Check client ID/secret
- `redirect_uri_mismatch` → Fix callback URL
- `access_denied` → User denied permission

## Next Steps

1. **Immediate**: Set up GitHub OAuth app and configure Supabase
2. **Testing**: Test the OAuth flow with a GitHub account
3. **Production**: Update redirect URLs for production domain
4. **Monitoring**: Monitor authentication logs in Supabase

## Files Modified

The GitHub integration is ready in:
- `frontend/public/pages/github-integration.html` - Main integration page
- `frontend/public/login.html` - Login page with GitHub OAuth
- `supabase_github_schema.sql` - Database schema for GitHub integration

All that's needed is the OAuth configuration in Supabase dashboard!