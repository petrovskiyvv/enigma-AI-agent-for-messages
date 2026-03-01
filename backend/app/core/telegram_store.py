from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.models import TelegramChannel, TelegramLinkToken


@dataclass
class LinkToken:
    token: str
    expires_at: str


class DbTelegramChannelStore:
    def create_link_token(self, ttl_minutes: int = 90) -> LinkToken:
        import uuid

        tok = str(uuid.uuid4())
        expires = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)

        with SessionLocal() as db:
            db.add(TelegramLinkToken(token=tok, expires_at=expires, consumed_at=None))
            db.commit()

        return LinkToken(token=tok, expires_at=expires.isoformat())

    def consume_token_and_register_channel(self, token: str, chat_id: int, title: str | None,
                                           chat_type: str | None) -> bool:
        ok = self.consume_link_token(token)
        if not ok:
            return False
        self.upsert_channel(chat_id=chat_id, chat_type=chat_type, title=title, active=True)
        return True

    def consume_link_token(self, token: str) -> bool:
        """Атомарно помечает токен использованным (если он существует и не истёк)."""
        now = datetime.now(timezone.utc)
        with SessionLocal() as db:
            row = db.get(TelegramLinkToken, token)
            if not row:
                return False
            if row.consumed_at is not None:
                return False
            expires = row.expires_at
            if getattr(expires, "tzinfo", None) is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires <= now:
                return False
            row.consumed_at = now
            db.add(row)
            db.commit()
            return True

    def upsert_channel(self, chat_id: int, chat_type: str | None, title: str | None, active: bool = True) -> None:
        now = datetime.now(timezone.utc)
        with SessionLocal() as db:
            cur = db.get(TelegramChannel, chat_id)
            if cur:
                cur.type = chat_type
                cur.title = title
                cur.active = active
                db.add(cur)
            else:
                db.add(TelegramChannel(
                    chat_id=chat_id,
                    type=chat_type,
                    title=title,
                    registered_at=now,
                    active=active,
                ))
            db.commit()

    def list_active_channels(self) -> list[dict]:
        with SessionLocal() as db:
            rows = db.execute(
                select(TelegramChannel).where(TelegramChannel.active.is_(True)).order_by(TelegramChannel.registered_at.desc())
            ).scalars().all()
            return [
                {
                    "chat_id": r.chat_id,
                    "type": r.type,
                    "title": r.title,
                    "registered_at": r.registered_at.isoformat(),
                    "active": r.active,
                }
                for r in rows
            ]


telegram_store = DbTelegramChannelStore()
