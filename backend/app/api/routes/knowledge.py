from __future__ import annotations

import asyncio
import logging
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.knowledge.loader import document_loader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

ALLOWED_EXTENSIONS = {".txt", ".docx", ".pdf"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

# Один executor — ограничиваем параллельность, чтобы не перегружать CPU/RAM
_executor = ThreadPoolExecutor(max_workers=2)


# ── In-memory хранилище статусов задач ───────────────────────────────────────

class JobStatus(str, Enum):
    PENDING   = "pending"
    PROCESSING = "processing"
    DONE      = "done"
    ERROR     = "error"


# { job_id: { status, source, chunks, error } }
_jobs: dict[str, dict] = {}


def _process_file(job_id: str, tmp_path: str, filename: str) -> None:
    """Выполняется в отдельном потоке — не блокирует event loop."""
    _jobs[job_id]["status"] = JobStatus.PROCESSING
    try:
        chunks_count = document_loader.load_file(
            path=tmp_path,
            source_name=filename,
        )
        _jobs[job_id].update({"status": JobStatus.DONE, "chunks": chunks_count})
        logger.info("Задача %s завершена: %d чанков", job_id, chunks_count)
    except Exception as exc:
        logger.exception("Ошибка задачи %s ('%s')", job_id, filename)
        _jobs[job_id].update({"status": JobStatus.ERROR, "error": str(exc)})
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ── Эндпоинты ─────────────────────────────────────────────────────────────────

@router.post("/upload", status_code=202)
async def upload_document(file: UploadFile = File(...)):
    """
    Принимает файл и ставит обработку в фоновую очередь.
    Возвращает job_id — клиент опрашивает /status/{job_id} для получения результата.
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

    # Сохраняем файл — поток прочитает его сам
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status": JobStatus.PENDING,
        "source": file.filename,
        "chunks": None,
        "error":  None,
    }

    # Запускаем обработку в пуле потоков — event loop не блокируется
    loop = asyncio.get_event_loop()
    loop.run_in_executor(_executor, _process_file, job_id, tmp_path, file.filename)

    logger.info("Задача %s создана для '%s'", job_id, file.filename)
    return {"job_id": job_id, "source": file.filename}


@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Возвращает текущий статус задачи обработки документа."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return {
        "job_id":  job_id,
        "status":  job["status"],
        "source":  job["source"],
        "chunks":  job["chunks"],
        "error":   job["error"],
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
