"""
Secure API Key Manager - Fetch and decrypt API keys from GitHub Gist
Sử dụng Fernet symmetric encryption để bảo vệ API keys khi public code lên GitHub.
"""
from cryptography.fernet import Fernet
import requests
import os
import logging
from typing import List, Optional
import base64
import json

logger = logging.getLogger(__name__)


class SecureKeyManager:
    """
    Quản lý API keys an toàn với encryption/decryption.
    
    Workflow:
    1. Tạo encryption key (1 lần): python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    2. Encrypt API keys và upload lên GitHub Gist (private)
    3. Backend fetch và decrypt khi khởi động
    
    Lưu ý:
    - ENCRYPTION_KEY phải được giữ bí mật (đặt trong .env, KHÔNG commit)
    - GitHub Gist có thể là private hoặc public (vì đã encrypt)
    - Nếu Gist fail, fallback về .env keys
    """
    
    def __init__(self):
        """Initialize key manager với encryption key từ .env"""
        self.encryption_key = os.getenv('ENCRYPTION_KEY', '')
        self.gist_url = os.getenv('GIST_API_KEYS_URL', '')
        
        # Validate encryption key format
        if self.encryption_key:
            try:
                self.fernet = Fernet(self.encryption_key.encode())
                logger.info("🔐 Encryption key loaded successfully")
            except Exception as e:
                logger.error(f"❌ Invalid encryption key format: {e}")
                self.fernet = None
        else:
            self.fernet = None
            logger.warning("⚠️ No encryption key found - using plain .env keys")
    
    def fetch_and_decrypt_keys(self) -> Optional[List[str]]:
        """
        Fetch encrypted keys từ GitHub Gist và decrypt.
        
        Returns:
            List of decrypted API keys hoặc None nếu fail
            
        Example Gist content (encrypted):
            {
                "version": "1.0",
                "encrypted_keys": "gAAAAABh...",
                "created_at": "2025-12-27"
            }
        """
        if not self.gist_url:
            logger.warning("⚠️ No GIST_API_KEYS_URL configured")
            return None
        
        if not self.fernet:
            logger.error("❌ Encryption not configured - cannot decrypt Gist keys")
            return None
        
        try:
            # Fetch from Gist
            logger.info(f"🌐 Fetching encrypted keys from GitHub Gist...")
            response = requests.get(self.gist_url, timeout=10)
            response.raise_for_status()
            
            # Parse JSON
            gist_data = response.json()
            encrypted_data = gist_data.get('encrypted_keys', '')
            
            if not encrypted_data:
                logger.error("❌ No encrypted_keys found in Gist")
                return None
            
            # Decrypt
            logger.info("🔓 Decrypting API keys...")
            decrypted_bytes = self.fernet.decrypt(encrypted_data.encode())
            decrypted_str = decrypted_bytes.decode('utf-8')
            
            # Parse comma-separated keys
            keys = [k.strip() for k in decrypted_str.split(',') if k.strip()]
            
            logger.info(f"✅ Successfully decrypted API keys from Gist")
            return keys
            
        except requests.RequestException as e:
            logger.error(f"❌ Failed to fetch from Gist: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to decrypt keys: {e}")
            return None
    
    def get_api_keys(self) -> List[str]:
        """
        Get API keys với fallback strategy:
        1. Try GitHub Gist (encrypted)
        2. Fallback to .env (plain)
        
        Returns:
            List of API keys
        """
        # Try Gist first
        gist_keys = self.fetch_and_decrypt_keys()
        if gist_keys:
            logger.info(f"✅ Using encrypted keys from GitHub Gist")
            return gist_keys
        
        # Fallback to .env
        logger.info("ℹ️ Falling back to .env API keys")
        env_keys = os.getenv('GROQ_API_KEYS', '')
        if not env_keys:
            logger.error("❌ No API keys found in .env either!")
            raise ValueError("No API keys configured! Set GIST_API_KEYS_URL or GROQ_API_KEYS")
        
        keys = [k.strip() for k in env_keys.split(',') if k.strip()]
        return keys
    
    @staticmethod
    def encrypt_keys_for_gist(keys: List[str], encryption_key: str) -> str:
        """
        Utility method: Encrypt API keys để upload lên Gist.
        
        Usage:
            >>> from utils.key_manager import SecureKeyManager
            >>> keys = ["key1", "key2", "key3"]
            >>> encryption_key = "your-fernet-key"
            >>> encrypted = SecureKeyManager.encrypt_keys_for_gist(keys, encryption_key)
            >>> print(encrypted)  # Upload this to Gist
        
        Args:
            keys: List of API keys
            encryption_key: Fernet encryption key
            
        Returns:
            Encrypted string để đưa vào Gist
        """
        fernet = Fernet(encryption_key.encode())
        keys_str = ','.join(keys)
        encrypted_bytes = fernet.encrypt(keys_str.encode())
        encrypted_str = encrypted_bytes.decode('utf-8')
        
        # Return JSON format for Gist
        gist_content = {
            "version": "1.0",
            "encrypted_keys": encrypted_str,
            "note": "Encrypted Groq API keys - Safe to public"
        }
        return json.dumps(gist_content, indent=2)
    
    @staticmethod
    def generate_encryption_key() -> str:
        """
        Utility method: Generate một encryption key mới.
        
        Usage:
            >>> from utils.key_manager import SecureKeyManager
            >>> key = SecureKeyManager.generate_encryption_key()
            >>> print(key)  # Save this in .env as ENCRYPTION_KEY
        
        Returns:
            Fernet encryption key
        """
        return Fernet.generate_key().decode()


# Singleton instance
secure_key_manager = SecureKeyManager()


if __name__ == "__main__":
    """
    Helper script để generate encryption key và encrypt API keys.
    
    Run: python -m utils.key_manager
    """
    print("🔐 Secure API Key Manager Setup")
    print("=" * 60)
    
    choice = input("\n1. Generate new encryption key\n2. Encrypt API keys for Gist\nChoice: ")
    
    if choice == "1":
        print("\n📝 Generating new Fernet encryption key...")
        key = SecureKeyManager.generate_encryption_key()
        print(f"\n✅ Encryption key generated:")
        print(f"   {key}")
        print(f"\n⚠️  IMPORTANT:")
        print(f"   1. Add to .env: ENCRYPTION_KEY={key}")
        print(f"   2. NEVER commit this key to GitHub!")
        print(f"   3. Keep it secret, keep it safe!")
        
    elif choice == "2":
        print("\n🔒 Encrypt API keys for GitHub Gist")
        
        # Get keys
        keys_input = input("\nEnter API keys (comma-separated): ")
        keys = [k.strip() for k in keys_input.split(',') if k.strip()]
        
        # Get encryption key
        enc_key = input("\nEnter encryption key (from step 1): ")
        
        try:
            encrypted_json = SecureKeyManager.encrypt_keys_for_gist(keys, enc_key)
            print(f"\n✅ Encrypted content for Gist:")
            print("=" * 60)
            print(encrypted_json)
            print("=" * 60)
            print(f"\n📤 Next steps:")
            print(f"   1. Create a GitHub Gist (private or public)")
            print(f"   2. Paste the above JSON content")
            print(f"   3. Get the 'raw' URL of the Gist")
            print(f"   4. Add to .env: GIST_API_KEYS_URL=<raw-gist-url>")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    else:
        print("Invalid choice!")
