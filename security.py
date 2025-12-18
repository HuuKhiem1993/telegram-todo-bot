import hashlib
import secrets
from datetime import datetime, timedelta

class Security:
    @staticmethod
    def generate_session_token():
        """Tạo token session ngẫu nhiên"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_password(password):
        """Hash mật khẩu"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return f"{salt}:{hash_obj.hex()}"
    
    @staticmethod
    def verify_password(stored_hash, password):
        """Xác minh mật khẩu"""
        salt, hash_value = stored_hash.split(':')
        new_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return secrets.compare_digest(hash_value, new_hash)
    
    @staticmethod
    def rate_limit_check(user_id, action, limit=5, period=60):
        """Kiểm tra rate limiting"""
        # Triển khai logic rate limiting
        pass