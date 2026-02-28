import asyncio
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.core.telegram_store import JsonTelegramChannelStore
from app.core.telegram_ticket_store import JsonTelegramTicketStore

TOKEN_RE = re.compile(r"\b[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}\b")

store = JsonTelegramChannelStore()
ticket_store = JsonTelegramTicketStore()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _extract_text(update: dict[str, Any]) -> tuple[int | None, str | None, str | None, str | None]:
    """Возвращает (chat_id, text, chat_title, chat_type) из update.
    Для канала актуально поле channel_post.
    """
    msg = update.get("channel_post") or update.get("message")
    if not msg:
        return None, None, None, None

    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    text = msg.get("text") or msg.get("caption")
    title = chat.get("title") or chat.get("username") or ""
    chat_type = chat.get("type") or ""
    return chat_id, text, title, chat_type


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
        elif et == "created":
            pass
        else:
            lines.append(f"• {ts} — {et}: {by}")
    return "\n".join(lines)


def _timeline_keyboard(ticket_id: str, assignee: str | None, actor: str | None = None) -> dict:
    """Inline-клавиатура для таймлайна в обсуждениях.

    - если заявка свободна -> показать "Взять в работу"
    - если заявка взята текущим пользователем -> показать "Отказаться от запроса"
    - если заявка взята кем-то другим -> оставить "Взять в работу" (это позволит перевзять, если так задумано)
    """
    if assignee is not None and actor is not None and assignee == actor:
        return {
            "inline_keyboard": [[{"text": "❌ Отказаться от запроса", "callback_data": f"decline:{ticket_id}"}]]
        }
    return {
        "inline_keyboard": [[{"text": "✅ Взять в работу", "callback_data": f"take:{ticket_id}"}]]
    }


async def _tg_call(client: httpx.AsyncClient, method: str, payload: dict) -> dict | None:
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/{method}"
    r = await client.post(url, json=payload)
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        return None
    return data.get("result")


async def _send_message(client: httpx.AsyncClient, chat_id: int, text: str) -> None:
    await _tg_call(client, "sendMessage", {"chat_id": chat_id, "text": text})


async def _handle_action_callback(client: httpx.AsyncClient, upd: dict[str, Any]) -> None:
    cq = upd.get("callback_query") or {}
    cq_id = cq.get("id")
    data = cq.get("data") or ""
    if not cq_id or not (data.startswith("take:") or data.startswith("decline:")):
        return

    action, ticket_id = data.split(":", 1)
    ticket_id = ticket_id.strip()
    t = ticket_store.get(ticket_id)
    if not t:
        await _tg_call(client, "answerCallbackQuery", {"callback_query_id": cq_id, "text": "Заявка не найдена в хранилище."})
        return

    user = cq.get("from") or {}
    uname = user.get("username")
    actor = f"@{uname}" if uname else (user.get("first_name") or "user")

    assignee = t.get("assignee")
    now = _utc_now_iso()

    if action == "decline":
        if assignee != actor:
            await _tg_call(client, "answerCallbackQuery", {"callback_query_id": cq_id, "text": "Отказаться может только текущий исполнитель."})
            return
        new_assignee = None
        ticket_store.upsert_ticket(ticket_id, {"assignee": None})
        ticket_store.add_event(ticket_id, {"ts": now, "type": "released", "by": actor})
        action_text = "Вы отказались от запроса"
    else:
        if assignee is None:
            new_assignee = actor
            ticket_store.upsert_ticket(ticket_id, {"assignee": new_assignee})
            ticket_store.add_event(ticket_id, {"ts": now, "type": "taken", "by": actor})
            action_text = "Взято в работу"
        elif assignee == actor:
            # на take повторно не снимаем — это делает отдельная кнопка decline
            await _tg_call(client, "answerCallbackQuery", {"callback_query_id": cq_id, "text": "У вас уже в работе. Используйте 'Отказаться от запроса'."})
            return
        else:
            prev = assignee
            new_assignee = actor
            ticket_store.upsert_ticket(ticket_id, {"assignee": new_assignee})
            ticket_store.add_event(ticket_id, {"ts": now, "type": "retaken", "by": actor, "prev": prev})
            action_text = f"Перевзято (было: {prev})"

    t2 = ticket_store.get(ticket_id) or t
    base_text = t2.get("base_text") or ""
    events2 = t2.get("events") or []

    ch_chat_id = t2.get("channel_chat_id")
    ch_msg_id = t2.get("channel_message_id")
    if ch_chat_id and ch_msg_id and base_text:
        await _tg_call(
            client,
            "editMessageText",
            {"chat_id": ch_chat_id, "message_id": ch_msg_id, "text": _format_channel_post(base_text, new_assignee)},
        )

    disc_chat_id = t2.get("discussion_chat_id")
    tl_msg_id = t2.get("timeline_message_id")
    if disc_chat_id and tl_msg_id:
        await _tg_call(
            client,
            "editMessageText",
            {
                "chat_id": disc_chat_id,
                "message_id": tl_msg_id,
                "text": _format_timeline(t2, events2),
                "reply_markup": _timeline_keyboard(ticket_id, new_assignee, actor=actor),
            },
        )

    await _tg_call(client, "answerCallbackQuery", {"callback_query_id": cq_id, "text": action_text})


def _match_ticket_for_auto_forward(msg: dict[str, Any]) -> str | None:
    """Пытается сопоставить auto-forward в linked discussion с заявкой.

    Ищем сообщение в linked-группе, которое Telegram автоматически форвардит из канала
    (is_automatic_forward=True). В этом update есть forward_from_chat + forward_from_message_id.
    """
    if not msg.get("is_automatic_forward"):
        return None

    chat = msg.get("chat") or {}
    discussion_chat_id = chat.get("id")
    fchat = msg.get("forward_from_chat") or {}
    from_chat_id = fchat.get("id")
    from_message_id = msg.get("forward_from_message_id")

    if discussion_chat_id is None or from_chat_id is None or from_message_id is None:
        return None

    for t in ticket_store.list_all():
        try:
            if int(t.get("discussion_chat_id") or 0) != int(discussion_chat_id):
                continue
            if int(t.get("channel_chat_id") or 0) != int(from_chat_id):
                continue
            if int(t.get("channel_message_id") or 0) != int(from_message_id):
                continue
            return str(t.get("ticket_id"))
        except Exception:
            continue
    return None


async def _handle_discussion_auto_forward(client: httpx.AsyncClient, upd: dict[str, Any]) -> None:
    """Когда появляется auto-forward поста канала в linked группе — создаём/обновляем таймлайн как комментарий."""
    msg = upd.get("message")
    if not isinstance(msg, dict):
        return

    ticket_id = _match_ticket_for_auto_forward(msg)
    if not ticket_id:
        return

    t = ticket_store.get(ticket_id)
    if not t:
        return

    discussion_root_message_id = msg.get("message_id")
    discussion_chat_id = (msg.get("chat") or {}).get("id")
    if discussion_root_message_id is None or discussion_chat_id is None:
        return

    ticket_store.upsert_ticket(ticket_id, {"discussion_root_message_id": discussion_root_message_id})

    events = t.get("events") or []
    tl_msg_id = t.get("timeline_message_id")
    if tl_msg_id:
        await _tg_call(
            client,
            "editMessageText",
            {
                "chat_id": discussion_chat_id,
                "message_id": tl_msg_id,
                "text": _format_timeline(t, events),
                "reply_markup": _timeline_keyboard(ticket_id, t.get("assignee")),
            },
        )
        return

    tl = await _tg_call(
        client,
        "sendMessage",
        {
            "chat_id": discussion_chat_id,
            "reply_to_message_id": discussion_root_message_id,
            "text": _format_timeline(t, events),
            "reply_markup": _timeline_keyboard(ticket_id, t.get("assignee")),
        },
    )
    if tl and tl.get("message_id"):
        ticket_store.upsert_ticket(ticket_id, {"timeline_message_id": tl.get("message_id")})


async def run_polling() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is empty")

    base = f"https://api.telegram.org/bot{settings.telegram_bot_token}"
    offset: int | None = None

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            try:
                payload: dict[str, Any] = {"timeout": 25}
                if offset is not None:
                    payload["offset"] = offset

                r = await client.get(f"{base}/getUpdates", params=payload)
                r.raise_for_status()
                data = r.json()
                if not data.get("ok"):
                    await asyncio.sleep(2)
                    continue

                for upd in data.get("result", []):
                    offset = upd.get("update_id", 0) + 1

                    # inline-кнопки
                    if upd.get("callback_query"):
                        try:
                            await _handle_action_callback(client, upd)
                        except Exception:
                            pass
                        continue

                    if upd.get("message"):
                        try:
                            await _handle_discussion_auto_forward(client, upd)
                        except Exception:
                            pass

                    chat_id, text, title, chat_type = _extract_text(upd)
                    if not chat_id or not text:
                        continue

                    m = TOKEN_RE.search(text)
                    if not m:
                        continue

                    token = m.group(0)
                    ok = store.consume_token_and_register_channel(
                        token=token,
                        chat_id=int(chat_id),
                        title=title,
                        chat_type=chat_type,
                    )
                    if ok:
                        await _send_message(client, int(chat_id), "✅ Канал подтверждён. Начинаю присылать новые заявки.")
                    else:
                        await _send_message(client, int(chat_id), "❌ Токен не найден или истёк. Сгенерируйте новый в веб-интерфейсе.")
            except Exception:
                await asyncio.sleep(2)


def main() -> None:
    asyncio.run(run_polling())


if __name__ == "__main__":
    main()
