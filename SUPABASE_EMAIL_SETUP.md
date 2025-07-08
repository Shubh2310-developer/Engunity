# 📧 Supabase Email Customization Guide

## Current Issue
- Emails are being sent from `noreply@mail.app.supabase.io`
- Need to customize to use "Engunity AI" branding
- Need to add Engunity AI logo to emails

## Solution Steps

### 1. **Supabase Dashboard Configuration**

1. Go to your Supabase project dashboard: https://supabase.com/dashboard/project/ckrtquhwlvpmpgrfemmb
2. Navigate to **Authentication** → **Settings**
3. Scroll down to **SMTP Settings**

### 2. **Custom SMTP Setup (Recommended)**

Configure custom SMTP to send emails from your domain:

```
SMTP Host: smtp.gmail.com (or your email provider)
SMTP Port: 587
SMTP User: your-email@yourdomain.com
SMTP Pass: your-app-password
From Email: noreply@engunity.ai
From Name: Engunity AI
```

### 3. **Email Templates Customization**

In Supabase Dashboard → Authentication → Email Templates:

#### **Confirm Signup Template:**
```html
<h2>Welcome to Engunity AI!</h2>
<p>Thanks for signing up! Follow this link to confirm your user:</p>
<p><a href="{{ .ConfirmationURL }}">Confirm your account</a></p>
<p>Best regards,<br>The Engunity AI Team</p>
```

#### **Reset Password Template:**
```html
<h2>Reset Your Engunity AI Password</h2>
<p>Follow this link to reset the password for your user:</p>
<p><a href="{{ .ConfirmationURL }}">Reset Password</a></p>
<p>If you didn't request this, please ignore this email.</p>
<p>Best regards,<br>The Engunity AI Team</p>
```

### 4. **Site URL Configuration**

Set your site URL in Supabase:
- Site URL: `https://yourdomain.com` or `http://localhost:3000` for development
- Redirect URLs: Add your production and development URLs

### 5. **Custom Email HTML Template with Logo**

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: 'Inter', sans-serif; margin: 0; padding: 0; background-color: #f8fafc; }
        .container { max-width: 600px; margin: 0 auto; background: white; }
        .header { background: linear-gradient(135deg, #1e293b, #374151); padding: 40px 20px; text-align: center; }
        .logo { width: 60px; height: 60px; margin: 0 auto 20px; }
        .content { padding: 40px 20px; }
        .button { background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🔮</div>
            <h1 style="color: white; margin: 0;">Engunity AI</h1>
        </div>
        <div class="content">
            <h2>{{ .Subject }}</h2>
            <p>{{ .Body }}</p>
            <a href="{{ .ConfirmationURL }}" class="button">{{ .ButtonText }}</a>
            <p style="margin-top: 40px; color: #6b7280; font-size: 14px;">
                Best regards,<br>
                The Engunity AI Team
            </p>
        </div>
    </div>
</body>
</html>
```

## Quick Fix for Development

If you can't set up custom SMTP immediately, you can customize the email templates in Supabase dashboard with better branding while keeping the default sender.