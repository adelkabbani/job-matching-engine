from cryptography.fernet import Fernet
import os
import base64

def get_cipher_suite():
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise ValueError("ENCRYPTION_KEY not found in environment variables.")
    return Fernet(key.encode())

def encrypt_value(value: str) -> str:
    """Encrypts a string value."""
    if not value: return None
    cipher_suite = get_cipher_suite()
    encrypted_bytes = cipher_suite.encrypt(value.encode())
    return encrypted_bytes.decode()

def decrypt_value(encrypted_value: str) -> str:
    """Decrypts an encrypted string value."""
    if not encrypted_value: return None
    cipher_suite = get_cipher_suite()
    decrypted_bytes = cipher_suite.decrypt(encrypted_value.encode())
    return decrypted_bytes.decode()

def generate_key():
    """Generates a new Fernet key."""
    return Fernet.generate_key().decode()
