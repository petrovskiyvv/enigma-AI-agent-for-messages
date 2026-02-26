import datetime
from typing import Optional


class TicketStore:
    def __init__(self):
        self._tickets: list[dict] = [
            {
                "id": 1,
                "created_at": "2026-02-25T09:14:00",
                "full_name": "Иванов Иван Иванович",
                "facility": "Завод №1, г. Казань",
                "phone": "+7 (999) 123-45-67",
                "email": "ivanov@zavod1.ru",
                "device_numbers": "12345, 67890",
                "device_type": "Газоанализатор ГС-812",
                "emotional_tone": "Негатив",
                "category": "Неисправность",
                "issue_summary": "Прибор не включается после плановой калибровки",
                "original_text": (
                    "Добрый день! Обращаюсь по поводу газоанализатора ГС-812 "
                    "(зав. №12345, 67890). После проведения плановой калибровки "
                    "прибор перестал включаться. Индикатор питания мигает красным. "
                    "Прошу срочно помочь, остановка производства несёт значительные убытки."
                ),
                "ai_response": (
                    "Уважаемый Иван Иванович!\n\n"
                    "По описанным симптомам рекомендуем:\n"
                    "1. Отключите прибор от сети на 30 секунд.\n"
                    "2. Проверьте давление калибровочного газа (0.5–1.5 бар).\n"
                    "3. Удерживайте кнопку MENU 10 секунд для сброса настроек.\n\n"
                    "С уважением, Служба технической поддержки ЭРИС"
                ),
                "status": "Новое",
            },
            {
                "id": 2,
                "created_at": "2026-02-25T11:30:00",
                "full_name": "Петрова Светлана Юрьевна",
                "facility": "ООО «ГазСнаб», г. Уфа",
                "phone": "+7 (347) 200-10-20",
                "email": "petrova@gazsnab.ru",
                "device_numbers": "А-2241",
                "device_type": "Газоанализатор ПГА-7",
                "emotional_tone": "Нейтраль",
                "category": "Документация",
                "issue_summary": "Запрос актуального паспорта на прибор ПГА-7",
                "original_text": (
                    "Здравствуйте. Просим предоставить актуальный паспорт и сертификат "
                    "соответствия на газоанализатор ПГА-7, заводской номер А-2241."
                ),
                "ai_response": (
                    "Уважаемая Светлана Юрьевна!\n\n"
                    "Паспорт и сертификат будут направлены на вашу почту в течение 1 рабочего дня.\n\n"
                    "С уважением, Служба технической поддержки ЭРИС"
                ),
                "status": "В работе",
            },
            {
                "id": 3,
                "created_at": "2026-02-26T08:05:00",
                "full_name": "Смирнов Алексей Петрович",
                "facility": "АО «НефтеХим», г. Нижнекамск",
                "phone": "+7 (855) 555-00-11",
                "email": "smirnov@neftekhim.ru",
                "device_numbers": "НК-001, НК-002, НК-003",
                "device_type": "Стационарный датчик СД-4М",
                "emotional_tone": "Позитив",
                "category": "Калибровка",
                "issue_summary": "Уточнение периодичности калибровки датчиков СД-4М",
                "original_text": (
                    "Добрый день! Хотим поблагодарить вашу команду за оперативную помощь. "
                    "Подскажите рекомендуемую периодичность калибровки для СД-4М. "
                    "Заводские номера: НК-001, НК-002, НК-003."
                ),
                "ai_response": (
                    "Уважаемый Алексей Петрович!\n\n"
                    "Для СД-4М рекомендуемая калибровка — каждые 6 месяцев (ГОСТ Р 52931). "
                    "При наличии агрессивных сред сократите до 3 месяцев.\n\n"
                    "С уважением, Служба технической поддержки ЭРИС"
                ),
                "status": "Закрыто",
            },
        ]
        self._next_id = 4

    def get_all(
        self,
        status: Optional[str] = None,
        tone: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[dict]:
        result = self._tickets.copy()

        if status:
            result = [t for t in result if t.get("status") == status]
        if tone:
            result = [t for t in result if t.get("emotional_tone") == tone]
        if category:
            result = [t for t in result if t.get("category") == category]
        if search:
            s = search.lower()
            result = [
                t for t in result
                if s in t.get("full_name", "").lower()
                or s in t.get("facility", "").lower()
                or s in t.get("issue_summary", "").lower()
                or s in t.get("device_numbers", "").lower()
            ]

        return result

    def get_by_id(self, ticket_id: int) -> Optional[dict]:
        return next((t for t in self._tickets if t["id"] == ticket_id), None)

    def add(self, ticket_data: dict) -> dict:
        ticket_data["id"] = self._next_id
        ticket_data["created_at"] = datetime.datetime.now().isoformat()
        self._tickets.append(ticket_data)
        self._next_id += 1
        return ticket_data

    def update(self, ticket_id: int, fields: dict) -> Optional[dict]:
        ticket = self.get_by_id(ticket_id)
        if ticket is None:
            return None
        ticket.update({k: v for k, v in fields.items() if v is not None})
        return ticket

    def stats(self) -> dict:
        by_tone: dict[str, int] = {}
        by_category: dict[str, int] = {}
        by_status: dict[str, int] = {}

        for t in self._tickets:
            tone = t.get("emotional_tone", "Нейтраль")
            cat = t.get("category", "Другое")
            status = t.get("status", "Новое")
            by_tone[tone] = by_tone.get(tone, 0) + 1
            by_category[cat] = by_category.get(cat, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total": len(self._tickets),
            "by_tone": by_tone,
            "by_category": by_category,
            "by_status": by_status,
        }


ticket_store = TicketStore()
