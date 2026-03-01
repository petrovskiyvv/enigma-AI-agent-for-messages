"""
email/imap_worker.py
Воркер входящей почты — забирает письма по IMAP и создаёт тикеты.

Запуск через docker-compose как отдельный сервис:
  command: ["python", "-m", "app.email.imap_worker"]
"""

from __future__ import annotations

import asyncio
import email
import imaplib
import logging
from email.header import decode_header as _decode_header

from app.core.config import settings
from app.services.telegram_notifier import notify_new_ticket

logger = logging.getLogger(__name__)


# ── Вспомогательные функции ───────────────────────────────────────────────────

def _decode_str(value: str | bytes | None) -> str:
    """Декодирует заголовок письма (может быть encoded-word)."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    parts = _decode_header(value)
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            result.append(str(part))
    return "".join(result)


def _extract_body(msg: email.message.Message) -> str:
    """Извлекает текстовое тело письма (text/plain предпочтительнее text/html)."""
    plain = ""
    html = ""

    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get("Content-Disposition", ""))
            if "attachment" in cd:
                continue
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            charset = part.get_content_charset() or "utf-8"
            decoded = payload.decode(charset, errors="replace")
            if ct == "text/plain" and not plain:
                plain = decoded
            elif ct == "text/html" and not html:
                html = decoded
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")
            if msg.get_content_type() == "text/plain":
                plain = text
            else:
                html = text

    if plain:
        return plain.strip()

    # Если есть только HTML — убираем теги (примитивно)
    if html:
        import re
        clean = re.sub(r"<[^>]+>", " ", html)
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

    return ""


def _build_full_text(msg: email.message.Message) -> tuple[str, str]:
    """
    Собирает полный текст для анализа и возвращает (full_text, sender_email).
    """
    subject = _decode_str(msg.get("Subject"))
    from_raw = _decode_str(msg.get("From", ""))
    body = _extract_body(msg)

    # Извлекаем email отправителя из заголовка From
    import re
    email_match = re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", from_raw)
    sender_email = email_match.group(0) if email_match else ""

    full_text = f"Тема: {subject}\nОт: {from_raw}\n\n{body}"
    return full_text, sender_email


# ── Обработка одного письма ───────────────────────────────────────────────────

async def _process_message(raw: bytes) -> None:
    msg = email.message_from_bytes(raw)
    full_text, sender_email = _build_full_text(msg)

    if not full_text.strip():
        logger.warning("Пустое письмо, пропускаем")
        return

    subject = _decode_str(msg.get("Subject", "(без темы)"))
    logger.info("Обрабатываем письмо: %s", subject)

    from app.services.ticket_service import TicketService
    service = TicketService()

    ticket = await service.create_from_email(full_text, sender_email=sender_email)
    await notify_new_ticket(ticket)
    logger.info("Создан тикет #%s из письма: %s", ticket.get("id"), subject)


# ── Основной цикл ─────────────────────────────────────────────────────────────

async def _poll_once() -> None:
    """Одна итерация: подключиться, забрать непрочитанные, отключиться."""
    with imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port) as imap:
        imap.login(settings.imap_user, settings.imap_password)
        imap.select(settings.imap_mailbox)

        _, msg_ids_raw = imap.search(None, "UNSEEN")
        msg_ids = msg_ids_raw[0].split() if msg_ids_raw[0] else []

        if not msg_ids:
            return

        logger.info("Найдено %d новых писем", len(msg_ids))

        for mid in msg_ids:
            try:
                _, data = imap.fetch(mid, "(RFC822)")
                raw = data[0][1]
                await _process_message(raw)
                # Помечаем как прочитанное только после успешной обработки
                imap.store(mid, "+FLAGS", "\\Seen")
            except Exception:
                logger.exception("Ошибка обработки письма %s", mid)
                # Не помечаем как прочитанное — попробуем снова


async def run_polling() -> None:
    if not settings.imap_host:
        logger.warning(
            "IMAP_HOST не задан — почтовый воркер не запущен. "
            "Укажите IMAP_HOST, IMAP_USER, IMAP_PASSWORD в .env"
        )
        return

    logger.info(
        "IMAP воркер запущен: %s:%d, ящик: %s, интервал: %ds",
        settings.imap_host, settings.imap_port,
        settings.imap_mailbox, settings.imap_poll_interval,
    )

    while True:
        try:
            await _poll_once()
        except imaplib.IMAP4.error as exc:
            logger.error("IMAP ошибка: %s", exc)
        except ConnectionError as exc:
            logger.error("Ошибка соединения: %s", exc)
        except Exception:
            logger.exception("Неожиданная ошибка в IMAP воркере")

        await asyncio.sleep(settings.imap_poll_interval)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(run_polling())


if __name__ == "__main__":
    main()
