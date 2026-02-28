from app.core.store import ticket_store
from app.schemas.ticket import TicketCreate, TicketUpdate
from app.services.analyzer import TextAnalyzer

analyzer = TextAnalyzer()


class TicketService:
    def get_list(self, status=None, tone=None, category=None, search=None) -> list[dict]:
        return ticket_store.get_all(status=status, tone=tone, category=category, search=search)

    def get_one(self, ticket_id: int) -> dict | None:
        return ticket_store.get_by_id(ticket_id)

    def create(self, data: TicketCreate) -> dict:
        text = data.original_text
        tone = analyzer.analyze_tone(text) if text else "Нейтральноно"
        category = analyzer.classify_category(text) if text else "Общий вопрос"

        return ticket_store.add({
            "full_name": data.full_name,
            "facility": data.facility,
            "phone": data.phone,
            "email": data.email,
            "device_numbers": data.device_numbers,
            "device_type": data.device_type,
            "original_text": text,
            "emotional_tone": tone,
            "category": category,
            "issue_summary": analyzer.summarize(text) if text else "",
            "ai_response": analyzer.generate_response(category) if text else "",
            "status": "Новое",
        })

    def update(self, ticket_id: int, data: TicketUpdate) -> dict | None:
        return ticket_store.update(ticket_id, data.dict(exclude_none=True))

    def analyze_and_create(self, text: str) -> dict:
        tone = analyzer.analyze_tone(text)
        category = analyzer.classify_category(text)

        return ticket_store.add({
            "full_name": analyzer.extract_name(text),
            "facility": "",
            "phone": analyzer.extract_phone(text),
            "email": analyzer.extract_email(text),
            "device_numbers": analyzer.extract_devices(text),
            "device_type": "",
            "original_text": text,
            "emotional_tone": tone,
            "category": category,
            "issue_summary": analyzer.summarize(text),
            "ai_response": analyzer.generate_response(category),
            "status": "Новое",
        })

    def get_stats(self) -> dict:
        return ticket_store.stats()
