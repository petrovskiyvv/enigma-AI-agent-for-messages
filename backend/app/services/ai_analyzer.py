from __future__ import annotations

import json
import logging
import re

from app.core.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
Ты — AI-ассистент службы технической поддержки компании ЭРИС (производитель газоанализаторов).
Твоя задача: проанализировать обращение клиента и вернуть структурированный JSON.

КОНТЕКСТ ИЗ БАЗЫ ЗНАНИЙ:
{knowledge}

ИНСТРУКЦИИ:
1. Извлеки все данные, которые явно указаны в письме. Если данных нет — оставь пустую строку.
2. Определи тональность по содержанию, а не по вежливым фразам.
3. Категория должна быть одной из: Неисправность, Калибровка, Документация, Интеграция, Доступ, Общий вопрос.
4. Черновик ответа пиши от лица службы поддержки ЭРИС, профессионально, на русском языке.

Верни ТОЛЬКО валидный JSON без markdown:
{
  "full_name": "ФИО или пустая строка",
  "phone": "телефон или пустая строка",
  "email": "email или пустая строка",
  "device_numbers": "заводские номера через запятую или пустая строка",
  "device_type": "модель/тип прибора или пустая строка",
  "emotional_tone": "Позитив" или "Нейтрально" или "Негатив",
  "category": "одна из категорий выше",
  "issue_summary": "суть проблемы в 1-2 предложениях",
  "ai_response": "готовый черновик ответа клиенту"
}\
"""


async def analyze_with_ai(text: str) -> dict:
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY не задан")

    from app.knowledge.retriever import get_relevant_context, knowledge_is_empty
    knowledge = (
        "База знаний пуста."
        if knowledge_is_empty()
        else get_relevant_context(text, top_k=4)
    )

    from groq import Groq
    client = Groq(api_key=settings.groq_api_key)

    response = client.chat.completions.create(
        model=settings.ai_model,
        messages=[
            {
                "role": "system",
                "content": _SYSTEM_PROMPT.format(knowledge=knowledge),
            },
            {
                "role": "user",
                "content": f"Письмо клиента:\n\n{text}",
            },
        ],
        response_format={"type": "json_object"},  # гарантирует валидный JSON
        temperature=0.3,   # меньше — стабильнее структура ответа
        max_tokens=1500,
    )

    raw = response.choices[0].message.content.strip()
    return json.loads(raw)


def _fallback_analyze(text: str) -> dict:
    from app.services.analyzer import TextAnalyzer
    az = TextAnalyzer()
    category = az.classify_category(text)
    return {
        "full_name":      az.extract_name(text),
        "phone":          az.extract_phone(text),
        "email":          az.extract_email(text),
        "device_numbers": az.extract_devices(text),
        "device_type":    "",
        "emotional_tone": az.analyze_tone(text),
        "category":       category,
        "issue_summary":  az.summarize(text),
        "ai_response":    az.generate_response(category),
    }


async def analyze_safe(text: str) -> dict:
    """Анализ с автофолбэком на keyword-анализатор при ошибке."""
    try:
        result = await analyze_with_ai(text)
        logger.info("AI-анализ выполнен (groq/%s)", settings.ai_model)
        return result
    except Exception as exc:
        logger.warning("Groq недоступен (%s), используем keyword-анализатор", exc)
        return _fallback_analyze(text)