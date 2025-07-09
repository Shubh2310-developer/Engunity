# GitHub OAuth Debug Instructions

## Current Issue
You're being redirected to GitHub for authorization, but after authorizing, you return to the sign-in prompt instead of seeing your repositories.

## Quick Debug Steps

### 1. Test OAuth Flow Directly
```bash
cd /home/ghost/engunity
python dev_server.py
```

Open: `http://localhost:8005/test_oauth_flow.html`

This page will help debug exactly what's happening during OAuth.

### 2. Test Steps
1. **Click "Test GitHub OAuth"** - should redirect to GitHub
2. **Authorize the app** on GitHub
3. **Return to page** - check the debug logs
4. **Click "Check Current Session"** - see if session exists

### 3. What Should Happen
After authorization, you should see:
- ✅ "GitHub OAuth successful for [username]"
- ✅ Active GitHub Session info box
- ✅ Provider token available

## Common Issues & Fixes

### Issue 1: Session Not Persisting
**Symptoms**: OAuth completes but session disappears
**Fix**: Check if redirect URL matches exactly

### Issue 2: No Provider Token
**Symptoms**: Session exists but no GitHub token
**Fix**: Check GitHub OAuth app scopes

### Issue 3: Infinite Sign-in Loop
**Symptoms**: Keeps showing sign-in prompt
**Fix**: Clear localStorage and try again

## Debug GitHub Integration Page

### 1. Clear Everything First
```javascript
// Open browser console and run:
localStorage.clear();
sessionStorage.clear();
```

### 2. Open GitHub Integration Page
Navigate to: `http://localhost:8005/pages/github-integration.html`

### 3. Check Console Messages
Look for these messages:
```
🔥 LOADING: GitHub Integration v2.0 - Timestamp: [time]
🚀 GitHub Integration page loaded - Version 2.0
✅ Supabase client initialized successfully
```

### 4. Try OAuth Again
1. Click "Sign in with GitHub (v2.0) 🚀"
2. Watch console for:
   ```
   🚀 GitHub OAuth initiated successfully - redirecting to GitHub...
   ```
3. After GitHub authorization, look for:
   ```
   🔄 Auth state changed: SIGNED_IN
   🎉 GitHub OAuth successful! Setting up...
   🔄 Re-checking authentication status...
   ✅ Active session found: [email]
   🔍 Checking for GitHub provider...
   GitHub provider found: true
   🎉 GitHub OAuth detected - setting up interface
   ```

## If OAuth Still Fails

### Method 1: Use Mock Login
- Click "Mock GitHub Login (Test Only)"
- This bypasses OAuth entirely and shows test data
- Confirms the interface works properly

### Method 2: Check Supabase Configuration
1. Go to Supabase Dashboard
2. Authentication → Providers
3. Verify GitHub is enabled
4. Check redirect URLs include your local domain

### Method 3: Check GitHub OAuth App
1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Verify Authorization callback URL is:
   `https://ckrtquhwlvpmpgrfemmb.supabase.co/auth/v1/callback`

## Expected Debug Output

### Successful OAuth Flow
```
🔥 LOADING: GitHub Integration v2.0 - Timestamp: 2025-07-09T17:08:41.000Z
🚀 GitHub Integration page loaded - Version 2.0 - 2025-07-09T17:08:41.000Z
✅ Supabase client initialized successfully
🚀 GitHub OAuth initiated successfully - redirecting to GitHub...
[User authorizes on GitHub]
🔄 Auth state changed: SIGNED_IN
🎉 GitHub OAuth successful! Setting up...
🔄 Re-checking authentication status...
✅ Active session found: user@example.com
🎉 GitHub OAuth detected - setting up interface
📊 Updating user info: {login: "username", email: "user@example.com", ...}
```

### Failed OAuth Flow
```
🔥 LOADING: GitHub Integration v2.0
❌ Session found but no GitHub provider
⚠️ Error checking profile: [error message]
```

## Quick Fixes

### Fix 1: Clear Browser Data
1. Press `Ctrl+Shift+Delete`
2. Clear "All time" data
3. Try OAuth again

### Fix 2: Use Incognito Mode
1. Open incognito/private window
2. Navigate to GitHub integration page
3. Try OAuth flow

### Fix 3: Check Network Tab
1. Open Developer Tools (F12)
2. Go to Network tab
3. Try OAuth flow
4. Look for failed requests

## Success Criteria

After successful OAuth:
- ✅ No sign-in prompt shown
- ✅ User info displayed (name, avatar)
- ✅ Repositories loading message
- ✅ GitHub repositories displayed
- ✅ No console errors

The debug page will help identify exactly where the OAuth flow is failing!