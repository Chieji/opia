"""Secure credential storage — keyring + encrypted file + env fallback."""
import asyncio
import json
import os
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64
import logging

logger = logging.getLogger(__name__)

OPIA_DIR = Path.home() / ".opia"
ENCRYPTED_FILE = OPIA_DIR / "credentials.enc"


class CredentialStorage:
    """Manages credential resolution: keyring → encrypted file → env var."""

    def __init__(self):
        OPIA_DIR.mkdir(parents=True, exist_ok=True)
        self._keyring_available = self._check_keyring()

    @staticmethod
    def _check_keyring() -> bool:
        try:
            import keyring
            keyring.get_password("opia_test", "test")
            return True
        except Exception:
            return False

    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
            backend=default_backend(),
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    @classmethod
    def _encrypt(cls, plaintext: str, password: str, salt: bytes) -> str:
        key = cls._derive_key(password, salt)
        f = Fernet(key)
        return f.encrypt(plaintext.encode()).decode()

    @classmethod
    def _decrypt(cls, ciphertext: str, password: str, salt: bytes) -> str:
        key = cls._derive_key(password, salt)
        f = Fernet(key)
        return f.decrypt(ciphertext.encode()).decode()

    def _load_encrypted_store(self) -> dict:
        if not ENCRYPTED_FILE.exists():
            return {}
        try:
            raw = ENCRYPTED_FILE.read_bytes()
            data = json.loads(raw)
            password = os.environ.get("OPIA_MASTER_KEY", "")
            salt = base64.urlsafe_b64decode(data["salt"].encode())
            return json.loads(
                self._decrypt(data["credentials"], password, salt)
            )
        except Exception as e:
            logger.debug(f"Failed to load encrypted store: {e}")
            return {}

    def _save_encrypted_store(self, credentials: dict) -> None:
        password = os.environ.get("OPIA_MASTER_KEY", "")
        salt = os.urandom(16)
        encrypted = self._encrypt(
            json.dumps(credentials),
            password,
            salt,
        )
        payload = json.dumps({
            "salt": base64.urlsafe_b64encode(salt).decode(),
            "credentials": encrypted,
        })
        ENCRYPTED_FILE.write_bytes(payload.encode())

    def get_credential(self, provider: str, keyring_service: str, env_var: str) -> Optional[str]:
        """Resolve credential with keyring -> encrypted file -> env fallback."""
        # 1. Keyring
        if self._keyring_available:
            try:
                import keyring
                cred = keyring.get_password(keyring_service, provider)
                if cred:
                    return cred
            except Exception as e:
                logger.debug(f"Keyring lookup failed for {provider}: {e}")

        # 2. Encrypted file
        store = self._load_encrypted_store()
        if provider in store:
            return store[provider]

        # 3. Environment variable
        return os.environ.get(env_var)

    async def aget_credential(self, provider: str, keyring_service: str, env_var: str) -> Optional[str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, self.get_credential, provider, keyring_service, env_var
        )

    def set_credential(self, provider: str, keyring_service: str, key: str) -> bool:
        """Store credential in keyring first, falling back to encrypted file."""
        # 1. Try keyring first
        if self._keyring_available:
            try:
                import keyring
                keyring.set_password(keyring_service, provider, key)
                return True
            except Exception as e:
                logger.debug(f"Keyring write failed for {provider}: {e}")

        # 2. Fallback to encrypted file
        store = self._load_encrypted_store()
        store[provider] = key
        try:
            self._save_encrypted_store(store)
            return True
        except Exception as e:
            logger.error(f"Failed to write encrypted credential for {provider}: {e}")
            return False

    async def aset_credential(self, provider: str, keyring_service: str, key: str) -> bool:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, self.set_credential, provider, keyring_service, key
        )

    def delete_credential(self, provider: str, keyring_service: str) -> None:
        """Remove from all stores."""
        if self._keyring_available:
            try:
                import keyring
                keyring.delete_password(keyring_service, provider)
            except Exception:
                pass
        store = self._load_encrypted_store()
        store.pop(provider, None)
        self._save_encrypted_store(store)

    async def adelete_credential(self, provider: str, keyring_service: str) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, self.delete_credential, provider, keyring_service
        )
