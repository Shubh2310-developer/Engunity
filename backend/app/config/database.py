"""Supabase configuration."""

import os
from supabase import create_client, Client
from .settings import settings

# Initialize Supabase client
supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_anon_key
)

def get_supabase() -> Client:
    """Get Supabase client instance."""
    return supabase

# For admin operations (server-side only)
def get_supabase_admin() -> Client:
    """Get Supabase admin client for server-side operations."""
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key
    )