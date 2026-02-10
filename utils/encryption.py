from cryptography.fernet import Fernet
import os
from config import ENCRYPTION_KEY # We need to add this to config.py

class Encryptor:
    """
    A simple wrapper around Fernet symmetric encryption.
    It expects the encryption key to be set as an environment variable.
    """
    def __init__(self, key: str):
        if not key:
            raise ValueError("ENCRYPTION_KEY must be set in the environment.")
        self.key = key.encode()
        self.fernet = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        """Encrypts a string."""
        if not data:
            return ""
        encrypted_data = self.fernet.encrypt(data.encode())
        return encrypted_data.decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypts a string."""
        if not encrypted_data:
            return ""
        decrypted_data = self.fernet.decrypt(encrypted_data.encode())
        return decrypted_data.decode()

# Initialize a global encryptor instance
encryptor = Encryptor(key=ENCRYPTION_KEY)
