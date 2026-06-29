"""Session tracking for active provider/model."""
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from opia.auth.storage import CredentialStorage

OPIA_DIR = Path.home() / ".opia"
SESSION_FILE = OPIA_DIR / "session.json"


@dataclass
class ActiveSession:
    provider: str = ""
    model: str = ""
    auth_status: str = "anonymous"
    last_used: str = ""
    created_at: str = ""


class SessionManager:
    """Manages active session state (NO credentials stored here)."""

    def __init__(self):
        OPIA_DIR.mkdir(parents=True, exist_ok=True)
        self._session: Optional[ActiveSession] = None
        self._load()

    def _load(self) -> None:
        if not SESSION_FILE.exists():
            self._session = ActiveSession()
            return
        try:
            with open(SESSION_FILE, "r") as f:
                data = json.load(f)
            self._session = ActiveSession(**data)
        except Exception:
            self._session = ActiveSession()

    def _save(self) -> None:
        if self._session is None:
            self._session = ActiveSession()
        with open(SESSION_FILE, "w") as f:
            json.dump(asdict(self._session), f, indent=2)

    def set_active(self, provider: str, model: Optional[str] = None) -> None:
        if self._session is None:
            self._session = ActiveSession()
        self._session.provider = provider
        if model:
            self._session.model = model
        self._session.last_used = datetime.now(timezone.utc).isoformat()
        self._session.auth_status = "authenticated"
        self._session.created_at = self._session.created_at or datetime.now(
            timezone.utc
        ).isoformat()
        self._save()

    def get_active(self) -> Optional[ActiveSession]:
        return self._session

    def clear(self) -> None:
        self._session = ActiveSession()
        self._save()

    @property
    def active_provider(self) -> str:
        return self._session.provider if self._session else ""

    @property
    def active_model(self) -> str:
        return self._session.model if self._session else ""
