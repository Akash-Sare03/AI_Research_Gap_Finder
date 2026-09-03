# backend/core/auth.py

import os
import json
import time
import hmac
import hashlib
import base64
import secrets
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from fastapi import HTTPException, Header, Depends, Request

from .config import Config

def hash_password(password: str) -> str:
    """Generate secure salted PBKDF2-SHA256 password hash."""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return f"{salt}${pwd_hash}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored salt$hash."""
    if not stored_hash or '$' not in stored_hash:
        return False
    try:
        salt, expected_hash = stored_hash.split('$', 1)
        actual_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return hmac.compare_digest(expected_hash, actual_hash)
    except Exception:
        return False

class UserStore:
    """Thread-safe persistent JSON user repository with password & workspace isolation."""
    
    def __init__(self, storage_path: Optional[str] = None):
        if storage_path:
            self.path = Path(storage_path)
        else:
            self.path = Path(Config.DATA_DIR) / "users.json"
        
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._save({})

    def _load(self) -> Dict[str, Dict[str, Any]]:
        try:
            if self.path.exists():
                with open(self.path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning loading user store: {e}")
        return {}

    def _save(self, data: Dict[str, Dict[str, Any]]):
        try:
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving user store: {e}")

    def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        normalized = email.strip().lower()
        users = self._load()
        return users.get(normalized)

    def register_user(self, email: str, password: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Register a new user or update password for existing account."""
        normalized = email.strip().lower()
        users = self._load()
        now_str = datetime.now().isoformat()
        pwd_hash = hash_password(password)
        
        if normalized in users:
            users[normalized]['password_hash'] = pwd_hash
            if name:
                users[normalized]['name'] = name.strip()
            users[normalized]['last_login'] = now_str
        else:
            users[normalized] = {
                'user_id': normalized,
                'email': normalized,
                'name': name.strip() if name else normalized.split('@')[0],
                'password_hash': pwd_hash,
                'auth_provider': 'password',
                'api_key': '',
                'created_at': now_str,
                'last_login': now_str
            }
        
        self._save(users)
        return self._sanitize_user(users[normalized])

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password."""
        normalized = email.strip().lower()
        users = self._load()
        user = users.get(normalized)
        now_str = datetime.now().isoformat()
        
        if not user:
            # Auto-create account seamlessly on sign in if new
            return self.register_user(normalized, password)
        
        stored_hash = user.get('password_hash', '')
        if not stored_hash:
            # User previously signed in via Google or guest: set password and log in
            user['password_hash'] = hash_password(password)
            user['last_login'] = now_str
            self._save(users)
            return self._sanitize_user(user)
        
        if not verify_password(password, stored_hash):
            return None
        
        user['last_login'] = now_str
        self._save(users)
        return self._sanitize_user(user)

    def authenticate_google_user(self, email: str, name: Optional[str] = None, picture: Optional[str] = None) -> Dict[str, Any]:
        """Sign in or register user via Google OAuth Identity."""
        normalized = email.strip().lower()
        users = self._load()
        now_str = datetime.now().isoformat()
        
        if normalized not in users:
            users[normalized] = {
                'user_id': normalized,
                'email': normalized,
                'name': name.strip() if name else normalized.split('@')[0],
                'picture': picture or '',
                'password_hash': '',
                'auth_provider': 'google',
                'api_key': '',
                'created_at': now_str,
                'last_login': now_str
            }
        else:
            users[normalized]['last_login'] = now_str
            if name:
                users[normalized]['name'] = name
            if picture:
                users[normalized]['picture'] = picture
        
        self._save(users)
        return self._sanitize_user(users[normalized])

    def set_user_api_key(self, email: str, api_key: str) -> Dict[str, Any]:
        """Save user's private Groq API key."""
        normalized = email.strip().lower()
        users = self._load()
        now_str = datetime.now().isoformat()
        
        if normalized not in users:
            users[normalized] = {
                'user_id': normalized,
                'email': normalized,
                'name': normalized.split('@')[0],
                'password_hash': '',
                'auth_provider': 'guest',
                'api_key': api_key.strip(),
                'created_at': now_str,
                'last_login': now_str
            }
        else:
            users[normalized]['api_key'] = api_key.strip()
        
        self._save(users)
        return self._sanitize_user(users[normalized])

    def _sanitize_user(self, user_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Return safe user dict without password hash."""
        return {
            'user_id': user_dict.get('user_id') or user_dict.get('email'),
            'email': user_dict.get('email'),
            'name': user_dict.get('name', ''),
            'picture': user_dict.get('picture', ''),
            'auth_provider': user_dict.get('auth_provider', 'password'),
            'has_api_key': bool(user_dict.get('api_key')),
            'masked_key': mask_api_key(user_dict.get('api_key')),
            'created_at': user_dict.get('created_at'),
            'last_login': user_dict.get('last_login')
        }

user_store = UserStore()

# -----------------------------------------------------------------------------
# Zero-Dependency HMAC-SHA256 Token Engine (JWT-Compatible)
# -----------------------------------------------------------------------------
def _b64_encode(data_bytes: bytes) -> str:
    return base64.urlsafe_b64encode(data_bytes).decode('utf-8').rstrip('=')

def _b64_decode(data_str: str) -> bytes:
    padding = '=' * (4 - (len(data_str) % 4)) if len(data_str) % 4 != 0 else ''
    return base64.urlsafe_b64decode((data_str + padding).encode('utf-8'))

def create_session_token(email: str, expires_days: int = 7) -> str:
    """Generate secure HMAC-SHA256 signed session token valid for 7 days."""
    normalized = email.strip().lower()
    header = {'alg': 'HS256', 'typ': 'JWT'}
    exp_ts = int(time.time()) + (expires_days * 86400)
    payload = {
        'sub': normalized,
        'email': normalized,
        'iat': int(time.time()),
        'exp': exp_ts
    }
    
    header_b64 = _b64_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = _b64_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    
    sign_target = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(Config.SECRET_KEY.encode('utf-8'), sign_target, hashlib.sha256).digest()
    sig_b64 = _b64_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def decode_session_token(token: str) -> Optional[str]:
    """Validate and decode session token, returning the user email if valid."""
    if not token or not isinstance(token, str):
        return None
    
    parts = token.strip().split('.')
    if len(parts) != 3:
        return None
    
    header_b64, payload_b64, sig_b64 = parts
    try:
        sign_target = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(Config.SECRET_KEY.encode('utf-8'), sign_target, hashlib.sha256).digest()
        provided_sig = _b64_decode(sig_b64)
        
        if not hmac.compare_digest(expected_sig, provided_sig):
            return None
        
        payload = json.loads(_b64_decode(payload_b64).decode('utf-8'))
        exp = payload.get('exp', 0)
        if time.time() > exp:
            return None
        
        return payload.get('email') or payload.get('sub')
    except Exception:
        return None

def validate_groq_api_key(api_key: str) -> Dict[str, Any]:
    """Ping Groq API to verify key validity before saving."""
    clean_key = str(api_key).strip()
    if not clean_key:
        return {'valid': False, 'message': 'API key cannot be empty.'}
    
    if not clean_key.startswith('gsk_'):
        return {'valid': False, 'message': 'Invalid Groq API key format. Groq keys start with "gsk_"'}
    
    try:
        from groq import Groq
        client = Groq(api_key=clean_key)
        resp = client.chat.completions.create(
            messages=[{'role': 'user', 'content': 'ping'}],
            model='openai/gpt-oss-20b',
            max_tokens=2
        )
        if resp and resp.choices:
            return {'valid': True, 'message': 'API Key verified successfully!'}
        return {'valid': False, 'message': 'Groq returned empty response.'}
    except Exception as e:
        err_msg = str(e)
        if '401' in err_msg or 'invalid_api_key' in err_msg.lower():
            return {'valid': False, 'message': 'Invalid API Key. Please check your key at console.groq.com'}
        elif '429' in err_msg or 'rate_limit' in err_msg.lower():
            return {'valid': True, 'message': 'API Key valid (currently rate limited on free tier).'}
        return {'valid': False, 'message': f'Groq connection error: {err_msg}'}

def mask_api_key(api_key: Optional[str]) -> str:
    if not api_key:
        return ''
    k = api_key.strip()
    if len(k) <= 8:
        return '***'
    return f"{k[:4]}...{k[-4:]}"

def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    if not authorization:
        return None
    
    token = authorization.replace('Bearer ', '').strip() if 'Bearer ' in authorization else authorization.strip()
    email = decode_session_token(token)
    if not email:
        return None
    
    user = user_store.get_user(email)
    if user:
        return user_store._sanitize_user(user)
    return None

def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    user = get_current_user_optional(authorization)
    if not user:
        raise HTTPException(
            status_code=401,
            detail='Session expired or authentication required. Please sign in.'
        )
    return user

class GuestQuotaTracker:
    """Tracks daily usage per guest session/client IP to allow 12 free trial operations."""
    
    def __init__(self, max_free_ops: int = 12):
        self.max_free_ops = max_free_ops
        self._usage: Dict[str, Dict[str, Any]] = {}
    
    def check_and_increment(self, client_id: str) -> Dict[str, Any]:
        today_str = datetime.now().strftime("%Y-%m-%d")
        record = self._usage.get(client_id, {"date": today_str, "count": 0})
        
        if record["date"] != today_str:
            record = {"date": today_str, "count": 0}
        
        if record["count"] >= self.max_free_ops:
            return {
                "allowed": False,
                "used": record["count"],
                "remaining": 0,
                "max": self.max_free_ops
            }
        
        record["count"] += 1
        self._usage[client_id] = record
        return {
            "allowed": True,
            "used": record["count"],
            "remaining": max(0, self.max_free_ops - record["count"]),
            "max": self.max_free_ops
        }

guest_quota = GuestQuotaTracker(max_free_ops=12)

def get_user_llm_key(request: Request, authorization: Optional[str] = Header(None)) -> Optional[str]:
    """
    Retrieve API key for active user.
    - If user has configured their own Groq API key: returns their personal key (unlimited).
    - If user is in Guest mode or has not configured a key: allows up to 12 free trial operations per day using the system developer API key.
    """
    user_data = get_current_user_optional(authorization)
    if user_data:
        full_user = user_store.get_user(user_data['email'])
        if full_user and full_user.get('api_key') and full_user['api_key'].strip():
            return full_user['api_key'].strip()
    
    # Guest or user without own custom key: check 12-trial quota
    client_ip = request.client.host if request.client else "unknown_client"
    client_id = user_data['email'] if user_data else f"guest_{client_ip}"
    
    quota_res = guest_quota.check_and_increment(client_id)
    if not quota_res["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=(
                "You have used your 12 free guest preview operations for today using the developer API key. "
                "To continue with unlimited PhD-level research analysis, please sign in or register with your email and add your free Groq API key (takes 30 seconds at console.groq.com)!"
            )
        )
    
    if not Config.GROQ_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="No developer preview key configured. Please enter your personal Groq API key in Settings."
        )
    
    return Config.GROQ_API_KEY
