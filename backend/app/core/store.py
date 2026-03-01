from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import or_, select, func, desc

from app.core.db import SessionLocal
from app.core.models import Ticket


def _to_dict(t: Ticket) -> dict[str, Any]:
    return {
        "id": t.id,
        "created_at": t.created_at.isoformat(),
        "full_name": t.full_name,
        "facility": t.facility,
        "phone": t.phone,
        "email": t.email,
        "device_numbers": t.device_numbers,
        "device_type": t.device_type,
        "emotional_tone": t.emotional_tone,
        "category": t.category,
        "issue_summary": t.issue_summary,
        "original_text": t.original_text,
        "ai_response": t.ai_response,
        "status": t.status,
    }


class DbTicketStore:
    def get_all(self, status=None, tone=None, category=None, search=None) -> list[dict[str, Any]]:
        with SessionLocal() as db:
            stmt = select(Ticket)

            if status:
                stmt = stmt.where(Ticket.status == status)
            if tone:
                stmt = stmt.where(Ticket.emotional_tone == tone)
            if category:
                stmt = stmt.where(Ticket.category == category)

            if search:
                s = f"%{search}%"
                stmt = stmt.where(
                    or_(
                        Ticket.full_name.ilike(s),
                        Ticket.facility.ilike(s),
                        Ticket.phone.ilike(s),
                        Ticket.email.ilike(s),
                        Ticket.device_numbers.ilike(s),
                        Ticket.device_type.ilike(s),
                        Ticket.issue_summary.ilike(s),
                        Ticket.original_text.ilike(s),
                    )
                )

            stmt = stmt.order_by(desc(Ticket.created_at), desc(Ticket.id))
            rows = db.execute(stmt).scalars().all()
            return [_to_dict(r) for r in rows]

    def get_by_id(self, ticket_id: int) -> dict[str, Any] | None:
        with SessionLocal() as db:
            row = db.get(Ticket, ticket_id)
            return _to_dict(row) if row else None

    def add(self, payload: dict[str, Any]) -> dict[str, Any]:
        with SessionLocal() as db:
            t = Ticket(
                created_at=payload.get("created_at") or datetime.now(timezone.utc).replace(tzinfo=None),
                full_name=payload.get("full_name"),
                facility=payload.get("facility"),
                phone=payload.get("phone"),
                email=payload.get("email"),
                device_numbers=payload.get("device_numbers"),
                device_type=payload.get("device_type"),
                emotional_tone=payload.get("emotional_tone"),
                category=payload.get("category") or "Общий вопрос",
                issue_summary=payload.get("issue_summary"),
                original_text=payload.get("original_text"),
                ai_response=payload.get("ai_response"),
                status=payload.get("status") or "Новое",
            )
            db.add(t)
            db.commit()
            db.refresh(t)
            return _to_dict(t)

    def update(self, ticket_id: int, patch: dict[str, Any]) -> dict[str, Any] | None:
        with SessionLocal() as db:
            t = db.get(Ticket, ticket_id)
            if not t:
                return None

            for k, v in patch.items():
                if v is None:
                    continue
                if hasattr(t, k):
                    setattr(t, k, v)

            db.add(t)
            db.commit()
            db.refresh(t)
            return _to_dict(t)

    def delete(self, ticket_id: int) -> bool:
        with SessionLocal() as db:
            t = db.get(Ticket, ticket_id)
            if not t:
                return False
            db.delete(t)
            db.commit()
            return True

    def stats(self) -> dict[str, Any]:
        with SessionLocal() as db:
            total = db.execute(select(func.count()).select_from(Ticket)).scalar_one()

            by_tone_rows = db.execute(select(Ticket.emotional_tone, func.count()).group_by(Ticket.emotional_tone)).all()
            by_cat_rows = db.execute(select(Ticket.category, func.count()).group_by(Ticket.category)).all()
            by_status_rows = db.execute(select(Ticket.status, func.count()).group_by(Ticket.status)).all()

            return {
                "total": total,
                "by_tone": {k or "": v for k, v in by_tone_rows},
                "by_category": {k or "": v for k, v in by_cat_rows},
                "by_status": {k or "": v for k, v in by_status_rows},
            }


ticket_store = DbTicketStore()
