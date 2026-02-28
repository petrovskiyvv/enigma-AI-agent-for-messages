import httpx

from app.core.config import settings
from app.core.telegram_store import JsonTelegramChannelStore
from app.core.telegram_ticket_store import JsonTelegramTicketStore

telegram_store = JsonTelegramChannelStore()
ticket_store = JsonTelegramTicketStore()


def _format_ticket_base(ticket: dict) -> str:
    lines = [
        "🆕 Новая заявка",
        f"ID: {ticket.get('id')}",
        f"Дата: {ticket.get('created_at')}",
        f"ФИО: {ticket.get('full_name') or ''}",
        f"Объект: {ticket.get('facility') or ''}",
        f"Телефон: {ticket.get('phone') or ''}",
        f"Email: {ticket.get('email') or ''}",
        f"Прибор: {ticket.get('device_type') or ''}",
        f"Зав.№: {ticket.get('device_numbers') or ''}",
        f"Категория: {ticket.get('category') or ''}",
        f"Тон: {ticket.get('emotional_tone') or ''}",
        "",
        f"Суть: {ticket.get('issue_summary') or ''}",
    ]
    return "\n".join(lines).strip()


def _format_channel_post(base_text: str, assignee: str | None) -> str:
    who = assignee or "—"
    return f"{base_text}\n\n👤 В работе: {who}"


def _format_timeline(ticket: dict, events: list[dict]) -> str:
    created_at = ticket.get("created_at") or "—"
    lines = ["🕒 Таймлайн", f"• {created_at} — пришло"]
    for e in (events or [])[-30:]:
        ts = e.get("ts") or "—"
        et = e.get("type") or "event"
        by = e.get("by") or "—"
        if et == "taken":
            lines.append(f"• {ts} — взял в работу: {by}")
        elif et == "released":
            lines.append(f"• {ts} — снял с работы: {by}")
        elif et == "retaken":
            prev = e.get("prev") or "—"
            lines.append(f"• {ts} — перевзял: {by} (было: {prev})")
        else:
            lines.append(f"• {ts} — {et}: {by}")
    return "\n".join(lines)


async def _tg_call(client: httpx.AsyncClient, method: str, payload: dict) -> dict | None:
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/{method}"
    r = await client.post(url, json=payload)
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        return None
    return data.get("result")


async def notify_new_ticket(ticket: dict) -> None:
    if not settings.telegram_bot_token:
        return

    channels = telegram_store.list_active_channels()
    if not channels:
        return

    ticket_id = str(ticket.get("id"))
    base_text = _format_ticket_base(ticket)
    post_text = _format_channel_post(base_text, assignee=None)

    async with httpx.AsyncClient(timeout=15.0) as client:
        for ch in channels:
            channel_chat_id = ch.get("chat_id")
            if channel_chat_id is None:
                continue

            try:
                sent = await _tg_call(
                    client,
                    "sendMessage",
                    {"chat_id": channel_chat_id, "text": post_text},
                )
                if not sent:
                    continue

                channel_message_id = sent.get("message_id")

                chat_info = await _tg_call(client, "getChat", {"chat_id": channel_chat_id})
                linked_chat_id = (chat_info or {}).get("linked_chat_id")

                discussion_root_message_id = None
                timeline_message_id = None

                ticket_store.upsert_ticket(
                    ticket_id=ticket_id,
                    payload={
                        "created_at": ticket.get("created_at"),
                        "base_text": base_text,
                        "channel_chat_id": channel_chat_id,
                        "channel_message_id": channel_message_id,
                        "discussion_chat_id": linked_chat_id,
                        "discussion_root_message_id": discussion_root_message_id,
                        "timeline_message_id": timeline_message_id,
                        "assignee": None,
                        "events": [],
                    },
                )
                ticket_store.add_event(ticket_id, {"ts": ticket.get("created_at"), "type": "created", "by": None})

            except Exception:
                pass
