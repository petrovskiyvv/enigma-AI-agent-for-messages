"""
knowledge/retriever.py
Семантический поиск по базе знаний.

Находит top_k наиболее релевантных чанков для заданного запроса
и возвращает их как строку-контекст для промпта LLM.
"""

from __future__ import annotations

import logging

from sqlalchemy import text

from app.core.db import SessionLocal

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
    return _model


def get_relevant_context(query: str, top_k: int = 4, min_similarity: float = 0.3) -> str:
    """
    Ищет top_k чанков, наиболее похожих на query.
    Возвращает форматированный текст для вставки в промпт.

    min_similarity — минимальный порог косинусного сходства (0..1).
    Чанки ниже порога отбрасываются.
    """
    try:
        model = _get_model()
        query_emb = model.encode(query).tolist()
    except Exception:
        logger.exception("Ошибка вычисления эмбеддинга запроса")
        return "База знаний временно недоступна."

    try:
        with SessionLocal() as db:
            # pgvector: <=> — косинусное расстояние (0 = идентично, 2 = противоположны)
            rows = db.execute(text("""
                SELECT source,
                       chunk_text,
                       1 - (embedding <=> :emb::vector) AS similarity
                FROM knowledge_chunks
                WHERE 1 - (embedding <=> :emb::vector) >= :min_sim
                ORDER BY embedding <=> :emb::vector
                LIMIT :k
            """), {
                "emb": query_emb,
                "k": top_k,
                "min_sim": min_similarity,
            }).fetchall()
    except Exception:
        logger.exception("Ошибка поиска в базе знаний")
        return "База знаний временно недоступна."

    if not rows:
        return "Релевантных материалов в базе знаний не найдено."

    parts = []
    for row in rows:
        parts.append(
            f"[Источник: {row.source} | Релевантность: {row.similarity:.0%}]\n"
            f"{row.chunk_text}"
        )

    return "\n\n---\n\n".join(parts)


def knowledge_is_empty() -> bool:
    """Проверяет, есть ли хоть что-то в базе знаний."""
    try:
        with SessionLocal() as db:
            count = db.execute(
                text("SELECT COUNT(*) FROM knowledge_chunks")
            ).scalar_one()
        return count == 0
    except Exception:
        return True
