from cryptography.fernet import Fernet
import os
import base64

def get_cipher_suite():
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        print("⚠️ WARNING: ENCRYPTION_KEY not found in environment variables. Data encryption is disabled.")
        return None
    try:
        return Fernet(key.encode())
    except Exception as e:
        print(f"⚠️ WARNING: Invalid ENCRYPTION_KEY: {e}")
        return None

def encrypt_value(value: str) -> str:
    """Encrypts a string value."""
    if not value: return None
    cipher_suite = get_cipher_suite()
    if not cipher_suite: return value # Fallback to plaintext
    try:
        # Don't encrypt if already encrypted (basic check)
        if value.startswith("gAAAAA"): 
            return value
        encrypted_bytes = cipher_suite.encrypt(value.encode())
        return encrypted_bytes.decode()
    except Exception as e:
        print(f"Encryption failed: {e}")
        return value

def decrypt_value(encrypted_value: str) -> str:
    """Decrypts an encrypted string value."""
    if not encrypted_value: return None
    cipher_suite = get_cipher_suite()
    if not cipher_suite: return encrypted_value
    try:
        decrypted_bytes = cipher_suite.decrypt(encrypted_value.encode())
        return decrypted_bytes.decode()
    except:
        # If it fails to decrypt, it might be plaintext from before encryption was introduced
        return encrypted_value

def generate_key():
    """Generates a new Fernet key."""
    return Fernet.generate_key().decode()

