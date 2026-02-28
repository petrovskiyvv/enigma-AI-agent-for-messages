from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.models import TelegramTicketBinding, TicketEvent


def _binding_to_dict(b: TelegramTicketBinding, events: list[TicketEvent] | None = None) -> dict[str, Any]:
    d: dict[str, Any] = {
        "ticket_id": str(b.ticket_id),
        "created_at": b.created_at.isoformat(),
        "base_text": b.base_text,
        "channel_chat_id": b.channel_chat_id,
        "channel_message_id": b.channel_message_id,
        "discussion_chat_id": b.discussion_chat_id,
        "discussion_root_message_id": b.discussion_root_message_id,
        "timeline_message_id": b.timeline_message_id,
        "assignee": b.assignee,
    }
    if events is not None:
        d["events"] = [
            {"ts": e.ts.isoformat(), "type": e.type, "by": e.by, "prev": e.prev}
            for e in events
        ]
    return d


class DbTelegramTicketStore:
    def upsert_ticket(self, ticket_id: str, payload: dict[str, Any]) -> None:
        tid = int(ticket_id)
        with SessionLocal() as db:
            cur = db.get(TelegramTicketBinding, tid)
            if not cur:
                cur = TelegramTicketBinding(
                    ticket_id=tid,
                    created_at=_parse_dt(payload.get("created_at")) or datetime.now(timezone.utc),
                )
            for k in [
                "base_text",
                "channel_chat_id",
                "channel_message_id",
                "discussion_chat_id",
                "discussion_root_message_id",
                "timeline_message_id",
                "assignee",
            ]:
                if k in payload:
                    setattr(cur, k, payload.get(k))
            db.add(cur)
            db.commit()

    def get(self, ticket_id: str) -> dict[str, Any] | None:
        tid = int(ticket_id)
        with SessionLocal() as db:
            b = db.get(TelegramTicketBinding, tid)
            if not b:
                return None
            events = db.execute(select(TicketEvent).where(TicketEvent.ticket_id == tid).order_by(TicketEvent.ts)).scalars().all()
            return _binding_to_dict(b, events)

    def list_all(self) -> list[dict[str, Any]]:
        with SessionLocal() as db:
            bindings = db.execute(select(TelegramTicketBinding)).scalars().all()
            out: list[dict[str, Any]] = []
            for b in bindings:
                events = db.execute(select(TicketEvent).where(TicketEvent.ticket_id == b.ticket_id).order_by(TicketEvent.ts)).scalars().all()
                out.append(_binding_to_dict(b, events))
            return out

    def add_event(self, ticket_id: str, event: dict[str, Any]) -> None:
        tid = int(ticket_id)
        with SessionLocal() as db:
            ts = _parse_dt(event.get("ts")) or datetime.now(timezone.utc)
            ev = TicketEvent(
                ticket_id=tid,
                ts=ts,
                type=event.get("type") or "unknown",
                by=event.get("by"),
                prev=event.get("prev"),
            )
            db.add(ev)
            db.commit()


def _parse_dt(v: Any) -> datetime | None:
    if not v:
        return None
    if isinstance(v, datetime):
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except Exception:
            return None
    return None


telegram_ticket_store = DbTelegramTicketStore()
