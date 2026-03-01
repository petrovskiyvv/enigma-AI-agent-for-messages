"""
knowledge/loader.py
Загружает документы в векторную БД (knowledge_chunks).

Поддерживаемые форматы: .txt, .docx, .pdf
Использует модель paraphrase-multilingual-MiniLM-L12-v2 (~120 MB, хорошо работает с русским)

Использование:
    from app.knowledge.loader import DocumentLoader
    loader = DocumentLoader()
    loader.load_file("path/to/doc.docx", source_name="Руководство ДГС-230")
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Generator

from sqlalchemy import text

from app.core.db import SessionLocal

logger = logging.getLogger(__name__)

# ── Ленивая загрузка модели эмбеддингов ───────────────────────────────────────
_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Загружаем модель эмбеддингов…")
        _model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        logger.info("Модель загружена")
    return _model


# ── Чтение файлов ─────────────────────────────────────────────────────────────

def _read_txt(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def _read_docx(path: str) -> str:
    from docx import Document
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _read_pdf(path: str) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return "\n".join(
                page.extract_text() or "" for page in pdf.pages
            )
    except ImportError:
        # Фолбэк через PyPDF2
        import PyPDF2
        text_parts = []
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts)


def read_file(path: str) -> str:
    """Читает файл и возвращает текст. Поддерживает .txt, .docx, .pdf"""
    suffix = Path(path).suffix.lower()
    if suffix == ".docx":
        return _read_docx(path)
    elif suffix == ".pdf":
        return _read_pdf(path)
    else:
        return _read_txt(path)


# ── Разбиение на чанки ─────────────────────────────────────────────────────────

def _split_into_chunks(
        text: str,
        chunk_size: int = 400,
        overlap: int = 60,
) -> list[str]:
    """
    Разбивает текст на куски по ~chunk_size слов с перекрытием overlap слов.
    Старается не разрывать предложения.
    """
    # Разбиваем на предложения
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks: list[str] = []
    current_words: list[str] = []

    for sentence in sentences:
        s_words = sentence.split()
        if len(current_words) + len(s_words) > chunk_size and current_words:
            chunks.append(" ".join(current_words))
            # Оставляем последние overlap слов для контекста
            current_words = current_words[-overlap:] if overlap else []
        current_words.extend(s_words)

    if current_words:
        chunks.append(" ".join(current_words))

    # Отфильтровываем слишком короткие чанки (< 20 слов) — мусор
    return [c for c in chunks if len(c.split()) >= 20]


# ── Сохранение в БД ───────────────────────────────────────────────────────────

def _save_chunks(source: str, chunks: list[str], embeddings) -> None:
    import json
    with SessionLocal() as db:
        # Удаляем старую версию документа
        db.execute(
            text("DELETE FROM knowledge_chunks WHERE source = :s"),
            {"s": source},
        )
        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            # Сохраняем эмбеддинг как JSON-строку — совместимо и без pgvector,
            # и с pgvector через ::vector cast в retriever.py
            emb_str = json.dumps(emb.tolist())
            db.execute(
                text("""
                    INSERT INTO knowledge_chunks (source, chunk_index, chunk_text, embedding)
                    VALUES (:source, :idx, :chunk, :emb)
                """),
                {
                    "source": source,
                    "idx": idx,
                    "chunk": chunk,
                    "emb": emb_str,
                },
            )
        db.commit()
    logger.info("Сохранено %d чанков для '%s'", len(chunks), source)


# ── Публичный интерфейс ───────────────────────────────────────────────────────

class DocumentLoader:
    def load_text(self, content: str, source_name: str) -> int:
        """
        Загружает текст напрямую (без файла).
        Возвращает количество созданных чанков.
        """
        chunks = _split_into_chunks(content)
        if not chunks:
            logger.warning("Документ '%s' не содержит текста", source_name)
            return 0

        model = _get_model()
        embeddings = model.encode(chunks, batch_size=32, show_progress_bar=False)
        _save_chunks(source_name, chunks, embeddings)
        return len(chunks)

    def load_file(self, path: str, source_name: str | None = None) -> int:
        """
        Читает файл, разбивает на чанки и сохраняет в БД.
        source_name по умолчанию = имя файла.
        """
        source = source_name or Path(path).name
        logger.info("Загружаем документ '%s' из %s", source, path)

        content = read_file(path)
        return self.load_text(content, source)

    def delete_document(self, source_name: str) -> int:
        """Удаляет все чанки документа. Возвращает количество удалённых."""
        with SessionLocal() as db:
            result = db.execute(
                text("DELETE FROM knowledge_chunks WHERE source = :s RETURNING id"),
                {"s": source_name},
            )
            count = result.rowcount
            db.commit()
        logger.info("Удалено %d чанков документа '%s'", count, source_name)
        return count

    def list_documents(self) -> list[dict]:
        """Возвращает список загруженных документов с количеством чанков."""
        with SessionLocal() as db:
            rows = db.execute(text("""
                SELECT source,
                       COUNT(*) AS chunks,
                       MAX(created_at) AS uploaded_at
                FROM knowledge_chunks
                GROUP BY source
                ORDER BY MAX(created_at) DESC
            """)).fetchall()
        return [
            {
                "source": r.source,
                "chunks": r.chunks,
                "uploaded_at": r.uploaded_at.isoformat() if r.uploaded_at else None,
            }
            for r in rows
        ]


# Синглтон для использования в других модулях
document_loader = DocumentLoader()