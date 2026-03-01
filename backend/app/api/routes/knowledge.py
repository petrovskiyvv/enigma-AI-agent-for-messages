"""
api/routes/knowledge.py
REST API для управления базой знаний.

POST   /api/knowledge/upload   — загрузить документ (.txt, .docx, .pdf)
GET    /api/knowledge/          — список загруженных документов
DELETE /api/knowledge/{source}  — удалить документ
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.knowledge.loader import document_loader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

ALLOWED_EXTENSIONS = {".txt", ".docx", ".pdf"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("/upload", status_code=201)
async def upload_document(file: UploadFile = File(...)):
    """
    Загружает документ в базу знаний.
    Поддерживаемые форматы: .txt, .docx, .pdf
    """
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Файл слишком большой. Максимум {MAX_FILE_SIZE // 1024 // 1024} MB",
        )

    # Сохраняем во временный файл — нужно для парсеров docx/pdf
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        chunks_count = document_loader.load_file(
            path=tmp_path,
            source_name=file.filename,
        )
    except Exception as exc:
        logger.exception("Ошибка загрузки документа '%s'", file.filename)
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {exc}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return {
        "source": file.filename,
        "chunks": chunks_count,
        "message": f"Документ '{file.filename}' загружен, создано {chunks_count} фрагментов",
    }


@router.get("")
async def list_documents():
    """Возвращает список загруженных документов."""
    return document_loader.list_documents()


@router.delete("/{source:path}", status_code=200)
async def delete_document(source: str):
    """Удаляет документ из базы знаний по имени."""
    count = document_loader.delete_document(source)
    if count == 0:
        raise HTTPException(status_code=404, detail=f"Документ '{source}' не найден")
    return {"deleted": count, "message": f"Удалено {count} фрагментов документа '{source}'"}
