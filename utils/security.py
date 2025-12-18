"""
utils/security.py
Security module: Handles Encryption and JWT Tokens.
Matches PDF Source 56: OAuth 2.0, Fernet encryption, JWT.
"""
from cryptography.fernet import Fernet
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
from typing import Optional, Dict

# Configuration
# In production, load these from environment variables!
SECRET_KEY = os.getenv("SECRET_KEY", "dev_orchestra_super_secret_key_2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Generate a consistent key for demo purposes (or load from env)
# If ENCRYPTION_KEY is not set, we generate one (warning: restarts will lose data access)
_env_key = os.getenv("ENCRYPTION_KEY")
if not _env_key:
    _key = Fernet.generate_key()
else:
    _key = _env_key.encode()

cipher_suite = Fernet(_key)

def encrypt_data(data: str) -> str:
    """Encrypt sensitive strings (like ADO PATs)."""
    if not data:
        return ""
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive strings."""
    if not encrypted_data:
        return ""
    try:
        return cipher_suite.decrypt(encrypted_data.encode()).decode()
    except Exception:
        return ""

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a JWT token for internal API communication."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None