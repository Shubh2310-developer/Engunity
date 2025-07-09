"""Cryptographic utilities for encrypting sensitive data."""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from ..config.settings import get_settings

# Global encryption key
_encryption_key = None

def get_encryption_key() -> bytes:
    """Get or generate the encryption key."""
    global _encryption_key
    
    if _encryption_key is None:
        settings = get_settings()
        
        # Use SECRET_KEY from settings or generate one
        secret_key = getattr(settings, 'SECRET_KEY', 'default-secret-key-change-in-production')
        
        # Derive a key from the secret
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'engunity-ai-salt',  # In production, use a random salt
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        _encryption_key = key
    
    return _encryption_key

def encrypt_text(text: str) -> str:
    """Encrypt a text string."""
    if not text:
        return text
    
    try:
        key = get_encryption_key()
        f = Fernet(key)
        encrypted = f.encrypt(text.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception as e:
        # If encryption fails, return original text (not recommended for production)
        return text

def decrypt_text(encrypted_text: str) -> str:
    """Decrypt an encrypted text string."""
    if not encrypted_text:
        return encrypted_text
    
    try:
        key = get_encryption_key()
        f = Fernet(key)
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode())
        decrypted = f.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        # If decryption fails, return original text (assume it's not encrypted)
        return encrypted_text

def hash_text(text: str) -> str:
    """Hash a text string using SHA256."""
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()

def verify_hash(text: str, hash_value: str) -> bool:
    """Verify a text against its hash."""
    return hash_text(text) == hash_value