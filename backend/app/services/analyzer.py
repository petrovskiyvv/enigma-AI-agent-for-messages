import re


class TextAnalyzer:
    _NEGATIVE_WORDS = [
        "срочно", "не работает", "сломан", "авария", "остановк",
        "убытк", "проблем", "ошибк", "не включ", "не запуск",
    ]
    _POSITIVE_WORDS = [
        "спасибо", "благодар", "отлично", "хорошо", "помогл",
    ]

    _CATEGORY_RULES: list[tuple[str, list[str]]] = [
        ("Документация", ["паспорт", "сертификат", "документ", "инструкц"]),
        ("Калибровка",   ["калибровк", "поверк", "настройк"]),
        ("Неисправность", ["не работает", "не включ", "сломан", "авария", "ошибк", "неисправ"]),
    ]

    _DEVICE_PATTERNS = [
        r'зав(?:одской)?\s*(?:номер|№|#)?\s*[:\s]*([\w\-,\s]+?)(?:[\.;]|$)',
        r'№\s*([\w\-]+)',
        r'\b([А-Я]{1,3}-\d{3,6})\b',
        r'\b(\d{5,6})\b',
    ]

    _RESPONSE_TEMPLATES: dict[str, str] = {
        "Неисправность": (
            "По описанным симптомам рекомендуем:\n"
            "1. Отключите прибор от сети на 30 секунд и снова включите.\n"
            "2. Проверьте целостность кабельных соединений.\n"
            "3. Убедитесь, что параметры питания соответствуют паспортным данным.\n\n"
            "Наш специалист свяжется с вами в течение 2 рабочих часов."
        ),
        "Калибровка": (
            "Согласно регламенту, плановая калибровка проводится каждые 6 месяцев. "
            "Для назначения выезда специалиста просим уточнить удобное время."
        ),
        "Документация": (
            "Запрошенные документы будут направлены на вашу электронную почту "
            "в течение 1 рабочего дня."
        ),
        "Общий вопрос": (
            "Ваш запрос принят и будет обработан в ближайшее время."
        ),
    }

    def analyze_tone(self, text: str) -> str:
        text_lower = text.lower()
        neg = sum(1 for w in self._NEGATIVE_WORDS if w in text_lower)
        pos = sum(1 for w in self._POSITIVE_WORDS if w in text_lower)
        if neg > pos:
            return "Негатив"
        if pos > neg:
            return "Позитив"
        return "Нейтраль"

    def classify_category(self, text: str) -> str:
        text_lower = text.lower()
        for category, keywords in self._CATEGORY_RULES:
            if any(kw in text_lower for kw in keywords):
                return category
        return "Общий вопрос"

    def extract_devices(self, text: str) -> str:
        found: set[str] = set()
        for pattern in self._DEVICE_PATTERNS:
            for match in re.findall(pattern, text, re.IGNORECASE):
                for part in re.split(r'[,\s]+', match.strip()):
                    part = part.strip(" .,;")
                    if len(part) >= 4:
                        found.add(part)
        return ", ".join(sorted(found))

    def extract_email(self, text: str) -> str:
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        return match.group(0) if match else ""

    def extract_phone(self, text: str) -> str:
        match = re.search(r'[\+7|8][\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}', text)
        return match.group(0) if match else ""

    def extract_name(self, text: str) -> str:
        patterns = [
            r'(?:с уважением|regards)[,\s]+([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)',
            r'(?:меня зовут|я,)\s+([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def summarize(self, text: str) -> str:
        first = text.split('.')[0].strip()
        return first[:97] + "..." if len(first) > 100 else first

    def generate_response(self, category: str) -> str:
        body = self._RESPONSE_TEMPLATES.get(category, self._RESPONSE_TEMPLATES["Общий вопрос"])
        return f"Уважаемый(-ая) клиент!\n\n{body}\n\nС уважением, Служба технической поддержки ЭРИС"
