# 🔐 OAuth Setup Guide for Engunity AI

## ❌ Current Error: `redirect_uri_mismatch`

The OAuth error you're seeing is because the redirect URIs aren't properly configured in your Supabase project and/or OAuth provider settings.

## 🔧 Step-by-Step Fix

### **1. Supabase Configuration**

#### **A. Get Your Supabase URLs**
Your Supabase project URLs should be:
- **Project URL**: `https://ckrtquhwlvpmpgrfemmb.supabase.co`
- **Auth Callback URL**: `https://ckrtquhwlvpmpgrfemmb.supabase.co/auth/v1/callback`

#### **B. Configure Site URL in Supabase**
1. Go to [Supabase Dashboard](https://supabase.com/dashboard/project/ckrtquhwlvpmpgrfemmb)
2. Navigate to **Authentication** → **Settings**
3. Set **Site URL** to your domain:
   - **Development**: `http://localhost:3000` or your local server
   - **Production**: `https://yourdomain.com`

#### **C. Add Redirect URLs**
In the same settings page, add these **Redirect URLs**:
```
http://localhost:3000/dashboard.html
http://localhost:8000/dashboard.html
https://yourdomain.com/dashboard.html
https://ckrtquhwlvpmpgrfemmb.supabase.co/auth/v1/callback
```

### **2. Google OAuth Configuration**

#### **A. Google Cloud Console Setup**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select your project
3. Enable **Google+ API** and **Google OAuth2 API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**

#### **B. Configure OAuth Client**
- **Application Type**: Web application
- **Name**: Engunity AI
- **Authorized JavaScript Origins**:
  ```
  http://localhost:3000
  http://localhost:8000
  https://yourdomain.com
  https://ckrtquhwlvpmpgrfemmb.supabase.co
  ```
- **Authorized Redirect URIs**:
  ```
  https://ckrtquhwlvpmpgrfemmb.supabase.co/auth/v1/callback
  http://localhost:3000/dashboard.html
  https://yourdomain.com/dashboard.html
  ```

#### **C. Add to Supabase**
1. Copy **Client ID** and **Client Secret**
2. In Supabase Dashboard → **Authentication** → **Providers**
3. Enable **Google** and paste the credentials

### **3. GitHub OAuth Configuration**

#### **A. GitHub App Setup**
1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click **New OAuth App**
3. Fill in details:
   - **Application Name**: Engunity AI
   - **Homepage URL**: `https://yourdomain.com`
   - **Authorization Callback URL**: `https://ckrtquhwlvpmpgrfemmb.supabase.co/auth/v1/callback`

#### **B. Add to Supabase**
1. Copy **Client ID** and **Client Secret**
2. In Supabase Dashboard → **Authentication** → **Providers**
3. Enable **GitHub** and paste the credentials

### **4. Testing URLs**

Use these URLs for testing:
- **Local Development**: `http://localhost:3000` or your dev server
- **Supabase Auth Callback**: `https://ckrtquhwlvpmpgrfemmb.supabase.co/auth/v1/callback`

### **5. Common Issues & Solutions**

#### **Error 400: redirect_uri_mismatch**
- ✅ Ensure all redirect URIs match exactly (including http/https)
- ✅ Add both your domain and Supabase callback URL
- ✅ Check for trailing slashes - they matter!

#### **Error 403: access_denied**
- ✅ Check OAuth app is not in development mode (for production)
- ✅ Verify OAuth scopes are properly configured
- ✅ Ensure user email is verified

#### **Error: Provider not configured**
- ✅ Enable the provider in Supabase Dashboard
- ✅ Add valid Client ID and Client Secret
- ✅ Save configuration changes

### **6. Quick Test**

After configuration, test with these steps:
1. Clear browser cache/cookies
2. Go to your login page
3. Click "Sign in with Google" or "Sign in with GitHub"
4. Should redirect to provider, then back to dashboard

### **7. Development vs Production**

#### **Development Setup**
```
Site URL: http://localhost:3000
Redirect URLs: 
- http://localhost:3000/dashboard.html
- https://ckrtquhwlvpmpgrfemmb.supabase.co/auth/v1/callback
```

#### **Production Setup**
```
Site URL: https://yourdomain.com
Redirect URLs:
- https://yourdomain.com/dashboard.html
- https://ckrtquhwlvpmpgrfemmb.supabase.co/auth/v1/callback
```

## 🎯 Final Checklist

- [ ] Supabase Site URL configured
- [ ] Supabase Redirect URLs added
- [ ] Google OAuth app created with correct URIs
- [ ] GitHub OAuth app created with correct callback
- [ ] OAuth providers enabled in Supabase
- [ ] Client IDs and secrets added to Supabase
- [ ] Browser cache cleared for testing

Once all items are checked, the OAuth login should work without redirect errors!