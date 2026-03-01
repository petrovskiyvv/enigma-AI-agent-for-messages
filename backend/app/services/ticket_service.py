from __future__ import annotations

from app.core.store import ticket_store
from app.schemas.ticket import TicketCreate, TicketUpdate
from app.services.analyzer import TextAnalyzer

analyzer = TextAnalyzer()


class TicketService:
    def get_list(self, status=None, tone=None, category=None, search=None) -> list[dict]:
        return ticket_store.get_all(
            status=status, tone=tone, category=category, search=search
        )

    def get_one(self, ticket_id: int) -> dict | None:
        return ticket_store.get_by_id(ticket_id)

    def create(self, data: TicketCreate) -> dict:
        """Создание тикета вручную (без AI — быстро, для ручного ввода)."""
        text = data.original_text
        tone = analyzer.analyze_tone(text) if text else "Нейтрально"
        category = analyzer.classify_category(text) if text else "Общий вопрос"

        return ticket_store.add({
            "full_name":      data.full_name,
            "facility":       data.facility,
            "phone":          data.phone,
            "email":          data.email,
            "device_numbers": data.device_numbers,
            "device_type":    data.device_type,
            "original_text":  text,
            "emotional_tone": tone,
            "category":       category,
            "issue_summary":  analyzer.summarize(text) if text else "",
            "ai_response":    analyzer.generate_response(category) if text else "",
            "status":         "Новое",
        })

    def update(self, ticket_id: int, data: TicketUpdate) -> dict | None:
        return ticket_store.update(ticket_id, data.dict(exclude_none=True))

    async def create_from_email(self, raw_text: str, sender_email: str = "") -> dict:
        """
        Создание тикета из входящего письма с AI-анализом.
        Использует Claude + RAG базу знаний.
        """
        from app.services.ai_analyzer import analyze_safe

        parsed = await analyze_safe(raw_text)

        # Если email не извлёкся из текста — берём из заголовка письма
        if not parsed.get("email") and sender_email:
            parsed["email"] = sender_email

        return ticket_store.add({
            **parsed,
            "original_text": raw_text,
            "status":        "Новое",
        })

    async def analyze_and_create(self, text: str) -> dict:
        """
        Используется эндпоинтом /api/analyze (ручной авто-анализ текста).
        """
        from app.services.ai_analyzer import analyze_safe

        parsed = await analyze_safe(text)
        return ticket_store.add({
            **parsed,
            "original_text": text,
            "status":        "Новое",
        })

    def get_stats(self) -> dict:
        return ticket_store.stats()
