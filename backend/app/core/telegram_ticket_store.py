import json
from pathlib import Path
from typing import Any

from app.core.config import settings


class JsonTelegramTicketStore:
    """Хранилище связок telegram-сообщений и статуса/истории заявки.

    Файл: settings.telegram_ticket_store_path (по умолчанию telegram_tickets.json)

    Структура:
    {
      "tickets": {
        "<ticket_id>": {
          "ticket_id": "...",
          "created_at": "...",
          "base_text": "...",               # оригинальный текст поста в канал
          "channel_chat_id": 123,
          "channel_message_id": 456,
          "discussion_chat_id": -100...,
          "discussion_root_message_id": 789,
          "timeline_message_id": 790,
          "assignee": "@user" | null,
          "events": [{"ts":"...","type":"created|taken|released|retaken","by":"@user"|null}]
        }
      }
    }
    """

    def __init__(self, path: str | None = None):
        base_dir = Path(__file__).resolve().parents[2]
        p = Path(path or settings.telegram_ticket_store_path)
        if not p.is_absolute():
            p = base_dir / p
        self._path = p
        self._data: dict[str, Any] = {"tickets": {}}
        self._last_mtime_ns: int | None = None

        if self._path.exists():
            self._load()
        else:
            self._persist()

    def _load(self) -> None:
        try:
            self._data = json.loads(self._path.read_text(encoding="utf-8"))
            if "tickets" not in self._data or not isinstance(self._data["tickets"], dict):
                self._data["tickets"] = {}
            try:
                self._last_mtime_ns = self._path.stat().st_mtime_ns
            except Exception:
                self._last_mtime_ns = None
        except Exception:
            self._data = {"tickets": {}}
            self._persist()

    def _persist(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
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

    def upsert_ticket(self, ticket_id: str, payload: dict[str, Any]) -> None:
        self._reload_if_changed()
        tickets = self._data.get("tickets", {})
        cur = tickets.get(ticket_id) or {}
        cur.update(payload)
        cur["ticket_id"] = ticket_id
        tickets[ticket_id] = cur
        self._data["tickets"] = tickets
        self._persist()

    def get(self, ticket_id: str) -> dict[str, Any] | None:
        self._reload_if_changed()
        return (self._data.get("tickets") or {}).get(ticket_id)

    def list_all(self) -> list[dict[str, Any]]:
        self._reload_if_changed()
        tickets = self._data.get("tickets") or {}
        return [v for v in tickets.values() if isinstance(v, dict)]

    def add_event(self, ticket_id: str, event: dict[str, Any]) -> None:
        self._reload_if_changed()
        t = (self._data.get("tickets") or {}).get(ticket_id)
        if not t:
            return
        ev = t.get("events")
        if not isinstance(ev, list):
            ev = []
        ev.append(event)
        t["events"] = ev
        self._data["tickets"][ticket_id] = t
        self._persist()
