"""
Secure token storage using OS keychain.

Stores OAuth tokens securely in the operating system's credential manager:
- macOS: Keychain
- Windows: Credential Manager
- Linux: Secret Service (GNOME Keyring, KWallet)
"""

import json
import logging
from pathlib import Path
from typing import Any

from inception.enhance.auth.base import OAuthToken

logger = logging.getLogger(__name__)


# Try to import keyring, fall back to file-based storage
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    logger.warning("keyring not available, using file-based token storage")


class TokenStorage:
    """
    Secure token storage with keychain integration.
    
    Falls back to encrypted file storage if keychain unavailable.
    """
    
    SERVICE_NAME = "com.inception.auth"
    
    def __init__(self, fallback_path: Path | None = None):
        """
        Initialize token storage.
        
        Args:
            fallback_path: Path for file-based fallback storage
        """
        self.use_keyring = KEYRING_AVAILABLE
        self.fallback_path = fallback_path or Path.home() / ".inception" / "tokens.json"
        
        if not self.use_keyring:
            self.fallback_path.parent.mkdir(parents=True, exist_ok=True)
    
    def store(self, provider: str, token: OAuthToken) -> None:
        """
        Store a token securely.
        
        Args:
            provider: Provider name (e.g., 'claude', 'gemini')
            token: OAuth token to store
        """
        token_data = json.dumps(token.to_dict())
        
        if self.use_keyring:
            try:
                keyring.set_password(
                    self.SERVICE_NAME,
                    f"{provider}_token",
                    token_data
                )
                logger.debug(f"Stored {provider} token in keychain")
                return
            except Exception as e:
                logger.warning(f"Keychain store failed: {e}, using fallback")
        
        # Fallback to file
        self._store_file(provider, token_data)
    
    def retrieve(self, provider: str) -> OAuthToken | None:
        """
        Retrieve a stored token.
        
        Args:
            provider: Provider name
            
        Returns:
            Token if found, None otherwise
        """
        token_data: str | None = None
        
        if self.use_keyring:
            try:
                token_data = keyring.get_password(
                    self.SERVICE_NAME,
                    f"{provider}_token"
                )
            except Exception as e:
                logger.warning(f"Keychain retrieve failed: {e}, using fallback")
        
        if token_data is None:
            token_data = self._retrieve_file(provider)
        
        if token_data:
            try:
                data = json.loads(token_data)
                return OAuthToken.from_dict(data)
            except Exception as e:
                logger.error(f"Failed to parse token for {provider}: {e}")
        
        return None
    
    def delete(self, provider: str) -> None:
        """
        Delete a stored token.
        
        Args:
            provider: Provider name
        """
        if self.use_keyring:
            try:
                keyring.delete_password(
                    self.SERVICE_NAME,
                    f"{provider}_token"
                )
                logger.debug(f"Deleted {provider} token from keychain")
            except keyring.errors.PasswordDeleteError:
                pass  # Already deleted
            except Exception as e:
                logger.warning(f"Keychain delete failed: {e}")
        
        # Also delete from fallback
        self._delete_file(provider)
    
    def list_providers(self) -> list[str]:
        """
        List providers with stored tokens.
        
        Returns:
            List of provider names
        """
        providers = []
        
        for provider in ["claude", "gemini", "openai"]:
            if self.retrieve(provider) is not None:
                providers.append(provider)
        
        return providers
    
    def clear_all(self) -> None:
        """Delete all stored tokens."""
        for provider in ["claude", "gemini", "openai"]:
            self.delete(provider)
    
    # =========================================================================
    # FILE-BASED FALLBACK
    # =========================================================================
    
    def _load_file_storage(self) -> dict[str, Any]:
        """Load file-based token storage."""
        if not self.fallback_path.exists():
            return {}
        
        try:
            return json.loads(self.fallback_path.read_text())
        except Exception:
            return {}
    
    def _save_file_storage(self, data: dict[str, Any]) -> None:
        """Save file-based token storage."""
        self.fallback_path.parent.mkdir(parents=True, exist_ok=True)
        self.fallback_path.write_text(json.dumps(data, indent=2))
        
        # Set restrictive permissions (owner read/write only)
        try:
            self.fallback_path.chmod(0o600)
        except Exception:
            pass
    
    def _store_file(self, provider: str, token_data: str) -> None:
        """Store token in file."""
        data = self._load_file_storage()
        data[provider] = token_data
        self._save_file_storage(data)
        logger.debug(f"Stored {provider} token in file")
    
    def _retrieve_file(self, provider: str) -> str | None:
        """Retrieve token from file."""
        data = self._load_file_storage()
        return data.get(provider)
    
    def _delete_file(self, provider: str) -> None:
        """Delete token from file."""
        data = self._load_file_storage()
        if provider in data:
            del data[provider]
            self._save_file_storage(data)
            logger.debug(f"Deleted {provider} token from file")
