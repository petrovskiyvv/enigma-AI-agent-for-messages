import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class LinkToken:
    token: str
    expires_at: str


class JsonTelegramChannelStore:
    """
    Хранилище привязанных Telegram-каналов и одноразовых токенов привязки.
    Формат файла: telegram_channels.json
    """

    def __init__(self, path: str | None = None):
        self._path = Path(path or settings.telegram_store_path)
        self._data: dict[str, Any] = {"channels": [], "pending_tokens": []}

        self._last_mtime_ns: int | None = None

        if self._path.exists():
            self._load()
        else:
            self._persist()

    def _load(self) -> None:
        try:
            self._data = json.loads(self._path.read_text(encoding="utf-8"))

            if "channels" not in self._data:
                self._data["channels"] = []
            if "pending_tokens" not in self._data:
                self._data["pending_tokens"] = []

            try:
                self._last_mtime_ns = self._path.stat().st_mtime_ns
            except Exception:
                self._last_mtime_ns = None
        except Exception:
            # если файл битый — не падаем, а пересоздаем пустой
            self._data = {"channels": [], "pending_tokens": []}
            self._persist()

    def _persist(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(self._path)

        try:
            self._last_mtime_ns = self._path.stat().st_mtime_ns
        except Exception:
            self._last_mtime_ns = None

    def _reload_if_changed(self) -> None:
        try:
            if not self._path.exists():
                return

            mtime_ns = self._path.stat().st_mtime_ns
            if self._last_mtime_ns is None or mtime_ns != self._last_mtime_ns:
                self._load()
        except Exception:
            return

    def _purge_expired_tokens(self) -> None:
        now = _utc_now()
        pending = []
        for t in self._data.get("pending_tokens", []):
            try:
                exp = datetime.fromisoformat(t["expires_at"])
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
            except Exception:
                continue
            if exp > now:
                pending.append(t)
        self._data["pending_tokens"] = pending

    def create_link_token(self) -> LinkToken:
        self._reload_if_changed()
        self._purge_expired_tokens()

        token = str(uuid.uuid4())
        exp = _utc_now() + timedelta(minutes=settings.telegram_link_token_ttl_minutes)
        entry = {"token": token, "expires_at": exp.isoformat()}
        self._data["pending_tokens"].append(entry)
        self._persist()
        return LinkToken(token=token, expires_at=entry["expires_at"])

    def consume_token_and_register_channel(
        self,
        token: str,
        chat_id: int,
        title: str | None,
        chat_type: str | None,
    ) -> bool:
        self._reload_if_changed()
        self._purge_expired_tokens()

        pending = self._data.get("pending_tokens", [])
        found = None
        for t in pending:
            if t.get("token") == token:
                found = t
                break
        if not found:
            return False

        self._data["pending_tokens"] = [t for t in pending if t.get("token") != token]

        channels = self._data.get("channels", [])
        existing = next((c for c in channels if c.get("chat_id") == chat_id), None)
        now = _utc_now().isoformat()
        payload = {
            "chat_id": chat_id,
            "type": chat_type or "channel",
            "title": title or "",
            "registered_at": now,
            "active": True,
        }
        if existing:
            existing.update(payload)
        else:
            channels.append(payload)
        self._data["channels"] = channels

        self._persist()
        return True

    def list_active_channels(self) -> list[dict[str, Any]]:
        self._reload_if_changed()
        channels = self._data.get("channels", [])
        return [c for c in channels if c.get("active") is True]