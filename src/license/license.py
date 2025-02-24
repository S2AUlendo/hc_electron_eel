from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os
import winreg
import requests
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

LICENSE_API_URL = "https://xpv5trebeqjttfw2vgysbnxnve0yfzbd.lambda-url.us-east-2.on.aws/"

class LicenseKey:
    
    def __init__(self):
        self.activated = False
        self.aes_key = self._load_or_generate_key("aes_key", 32)
        self.iv = self._load_or_generate_key("iv", 16)
        self.encrypted_key = None
        self.feature = 0
        self.days_remaining = 0
        self.license_key = self._load_saved_license_key()

    def _load_saved_license_key(self):
        self.encrypted_key = self.read_from_registry("Software\\Ulendo", "encrypted_key")
        if self.encrypted_key:
            try:
                return self.decrypt_license_key(self.encrypted_key)
            except Exception as e:
                logger.error(f"Failed to decrypt license key: {e}")
                raise e
        return None
        
    def _load_or_generate_key(self, key_name, length):
        key = self.read_from_registry("Software\\Ulendo", key_name)
        if key:
            return key
        key = os.urandom(length)
        self.write_to_registry("Software\\Ulendo", key_name, key)
        return key
    
    def set_license_key(self, license_key):
        self.license_key = license_key
        
    # Encrypting the license key
    def encrypt_license_key(self, license_key: str) -> bytes:
        # Pad the data to match AES block size
        padder = padding.PKCS7(128).padder()  # 128 for AES block size
        padded_data = padder.update(license_key.encode()) + padder.finalize()

        # Initialize AES cipher
        cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(self.iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Encrypt the padded data
        encrypted_license_key = encryptor.update(padded_data) + encryptor.finalize()

        return encrypted_license_key

    # Decrypting the license key
    def decrypt_license_key(self, encrypted_license_key: bytes) -> str:
        # Initialize AES cipher for decryption
        cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(self.iv), backend=default_backend())
        decryptor = cipher.decryptor()

        # Decrypt the encrypted data
        decrypted_data = decryptor.update(encrypted_license_key) + decryptor.finalize()

        # Unpad the decrypted data
        unpadder = padding.PKCS7(128).unpadder()
        license_key = unpadder.update(decrypted_data) + unpadder.finalize()

        return license_key.decode()

    # Windows Registry helpers
    def write_to_registry(self, key_path: str, value_name: str, value: bytes):
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as reg_key:
                winreg.SetValueEx(reg_key, value_name, 0, winreg.REG_BINARY, value)
            print(f"Data successfully written to registry at {key_path}\\{value_name}.")
        except Exception as e:
            print(f"Failed to write to registry: {e}")
            raise e

    def read_from_registry(self, key_path: str, value_name: str) -> bytes:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as reg_key:
                value, regtype = winreg.QueryValueEx(reg_key, value_name)
                return value
        except FileNotFoundError:
            print(f"No value found at {key_path}\\{value_name}.")
            return None
        except Exception as e:
            print(f"Failed to read from registry: {e}")
            return None
    
    def activate_license_from_cloud(self):
        payload = {"action": "activate", "license_key": self.license_key}
        try:
            response = requests.post(LICENSE_API_URL, json=payload)
            status = response.json().get("status", {})
            
            if response.status_code == 200 and status == "success":
                self.feature = response.json().get("feature", {})
                self.encrypted_key = self.encrypt_license_key(self.license_key)
                self.write_to_registry("Software\\Ulendo", "encrypted_key", self.encrypted_key)
                self.activated = True
            else:
                self.activated = False
        except Exception as e:
            print(f"Error during activation: {e}")
            raise e
                
    def check_license_from_cloud(self):
        payload = {"action": "check", "license_key": self.license_key}
        try:
            response = requests.post(LICENSE_API_URL, json=payload)
            logger.info(f"License check response: {response.text}")
            status = response.json().get("status", {})
            
            if response.status_code == 200 and status == "success":
                self.feature = response.json().get("feature", {})
                self.activated = True
            else:
                self.activated = False
        except Exception as e:
            print(f"Error during license check: {e}")
            self.activated = False
            raise e
            
    def get_license_day_remaining(self):
        payload = {"action": "days_remaining", "license_key": self.license_key}
        try:
            response = requests.post(LICENSE_API_URL, json=payload)
            status = response.json().get("status", {})
            
            if response.status_code == 200 and status == "success":
                self.days_remaining = response.json().get("days_remaining", {})
            else:
                self.days_remaining = 0
        except Exception as e:
            print(f"Error during license check: {e}")
            self.days_remaining = 0
            raise e
            
        