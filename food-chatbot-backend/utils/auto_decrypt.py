"""
Auto Decrypt Module - Tự động decrypt API keys từ GitHub Gist
Được gọi tự động khi backend khởi động

Workflow:
1. Đọc GIST_URL_KEY và ENCRYPTED_GIST_URL từ .env
2. Decrypt Gist URL
3. Fetch encrypted keys từ Gist
4. Decrypt tất cả API keys
5. Inject vào os.environ để backend sử dụng
"""

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64
import os
import json
import requests
import logging

logger = logging.getLogger(__name__)


class AutoDecryptService:
    """Service tự động decrypt và load API keys"""
    
    def __init__(self):
        self.gist_url_key = os.getenv('GIST_URL_KEY', '')
        self.encrypted_gist_url = os.getenv('ENCRYPTED_GIST_URL', '')
        
    def decrypt_gist_url(self):
        """Decrypt Gist URL từ config"""
        if not self.gist_url_key or not self.encrypted_gist_url:
            logger.warning("⚠️  GIST_URL_KEY hoặc ENCRYPTED_GIST_URL không được cấu hình")
            return None
        
        try:
            # Decode key và encrypted data
            aes_key = base64.b64decode(self.gist_url_key)
            combined = base64.b64decode(self.encrypted_gist_url)
            
            # Extract nonce và encrypted data
            nonce = combined[:12]
            encrypted_data = combined[12:]
            
            # Decrypt
            aesgcm = AESGCM(aes_key)
            decrypted_url = aesgcm.decrypt(nonce, encrypted_data, None)
            
            logger.info("✅ Gist URL decrypted successfully")
            return decrypted_url.decode('utf-8')
            
        except Exception as e:
            logger.error(f"❌ Error decrypting Gist URL: {e}")
            return None
    
    def fetch_encrypted_keys_from_gist(self, gist_url):
        """Fetch encrypted keys từ GitHub Gist"""
        try:
            logger.info(f"🌐 Fetching encrypted keys from Gist...")
            response = requests.get(gist_url, timeout=10)
            response.raise_for_status()
            
            # Clean response text (remove trailing %% or % from Gist)
            response_text = response.text.strip()
            # Remove any trailing % characters
            while response_text.endswith('%'):
                response_text = response_text[:-1].strip()
            
            gist_data = json.loads(response_text)
            logger.info("✅ Gist data fetched successfully")
            return gist_data
            
        except Exception as e:
            logger.error(f"❌ Error fetching Gist: {e}")
            return None
    
    def decrypt_api_keys(self, gist_data):
        """Decrypt API keys từ Gist data"""
        try:
            decryption_key_b64 = gist_data.get('decryption_key', '')
            encrypted_keys_list = gist_data.get('encrypted_keys', [])
            
            if not decryption_key_b64 or not encrypted_keys_list:
                logger.error("❌ Invalid Gist data format")
                return []
            
            # Decode decryption key
            aes_key = base64.b64decode(decryption_key_b64)
            aesgcm = AESGCM(aes_key)
            
            # Decrypt each key
            decrypted_keys = []
            for encrypted_key_b64 in encrypted_keys_list:
                combined = base64.b64decode(encrypted_key_b64)
                nonce = combined[:12]
                encrypted_data = combined[12:]
                
                decrypted_key = aesgcm.decrypt(nonce, encrypted_data, None)
                decrypted_keys.append(decrypted_key.decode('utf-8'))
            
            logger.info(f"✅ Decrypted {len(decrypted_keys)} API keys")
            return decrypted_keys
            
        except Exception as e:
            logger.error(f"❌ Error decrypting API keys: {e}")
            return []
    
    def load_api_keys(self):
        """
        Main method: Decrypt và load API keys vào environment
        
        Returns:
            List of API keys hoặc None nếu fail
        """
        logger.info("🔓 Starting auto-decrypt process...")
        
        # Step 1: Decrypt Gist URL
        gist_url = self.decrypt_gist_url()
        if not gist_url:
            logger.warning("⚠️  Fallback to plaintext GROQ_API_KEYS from .env")
            plaintext_keys = os.getenv('GROQ_API_KEYS', '')
            if plaintext_keys:
                return [k.strip() for k in plaintext_keys.split(',') if k.strip()]
            return None
        
        # Step 2: Fetch encrypted keys from Gist
        gist_data = self.fetch_encrypted_keys_from_gist(gist_url)
        if not gist_data:
            logger.warning("⚠️  Fallback to plaintext GROQ_API_KEYS from .env")
            plaintext_keys = os.getenv('GROQ_API_KEYS', '')
            if plaintext_keys:
                return [k.strip() for k in plaintext_keys.split(',') if k.strip()]
            return None
        
        # Step 3: Decrypt API keys
        api_keys = self.decrypt_api_keys(gist_data)
        if not api_keys:
            logger.warning("⚠️  Fallback to plaintext GROQ_API_KEYS from .env")
            plaintext_keys = os.getenv('GROQ_API_KEYS', '')
            if plaintext_keys:
                return [k.strip() for k in plaintext_keys.split(',') if k.strip()]
            return None
        
        # Step 4: Inject vào environment
        os.environ['GROQ_API_KEYS'] = ','.join(api_keys)
        logger.info(f"✅ {len(api_keys)} API keys loaded and injected into environment")
        
        return api_keys


# Singleton instance
auto_decrypt_service = AutoDecryptService()


def auto_load_api_keys():
    """
    Helper function để gọi từ main.py
    Tự động decrypt và load API keys khi backend khởi động
    """
    return auto_decrypt_service.load_api_keys()
