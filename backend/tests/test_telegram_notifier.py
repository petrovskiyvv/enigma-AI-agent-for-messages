from __future__ import annotations

import pytest


def test_format_ticket_base_contains_key_fields():
    from app.services import telegram_notifier

    t = {
        "id": 1,
        "created_at": "2030-01-01",
        "full_name": "Иван",
        "facility": "Завод",
        "issue_summary": "Не работает",
    }
    text = telegram_notifier._format_ticket_base(t)
    assert "🆕 Новая заявка" in text
    assert "ID: 1" in text
    assert "Суть:" in text


@pytest.mark.asyncio
async def test_notify_new_ticket_creates_ticket_record(tmp_path, monkeypatch):
    from app.services import telegram_notifier
    from app.core.config import settings
    from app.core.telegram_ticket_store import JsonTelegramTicketStore

    monkeypatch.setattr(settings, "telegram_bot_token", "TEST")

    ts = JsonTelegramTicketStore(path=str(tmp_path / "tickets.json"))
    monkeypatch.setattr(telegram_notifier, "ticket_store", ts)

    class DummyChannelStore:
        def list_active_channels(self):
            return [{"chat_id": -123}]

    monkeypatch.setattr(telegram_notifier, "telegram_store", DummyChannelStore())

    calls: list[tuple[str, dict]] = []

    async def fake_tg_call(_client, method: str, payload: dict):
        calls.append((method, payload))
        if method == "sendMessage":
            return {"message_id": 42}
        if method == "getChat":
            return {"linked_chat_id": -999}
        return {"ok": True}

    monkeypatch.setattr(telegram_notifier, "_tg_call", fake_tg_call)

    ticket = {
        "id": 7,
        "created_at": "2030-01-01T00:00:00Z",
        "full_name": "Иванов Иван",
        "facility": "X",
        "issue_summary": "Y",
    }
    await telegram_notifier.notify_new_ticket(ticket)

    assert any(m == "sendMessage" for m, _ in calls)
    assert any(m == "getChat" for m, _ in calls)

    rec = ts.get("7")
    assert rec["channel_chat_id"] == -123
    assert rec["channel_message_id"] == 42
    assert rec["discussion_chat_id"] == -999
    assert any(e["type"] == "created" for e in rec["events"])


@pytest.mark.asyncio
async def test_notify_new_ticket_no_token_or_no_channels_is_noop(monkeypatch):
    from app.services import telegram_notifier
    from app.core.config import settings

    monkeypatch.setattr(settings, "telegram_bot_token", "")
    await telegram_notifier.notify_new_ticket({"id": 1})

    monkeypatch.setattr(settings, "telegram_bot_token", "TEST")

    class DummyChannelStore:
        def list_active_channels(self):
            return []

    monkeypatch.setattr(telegram_notifier, "telegram_store", DummyChannelStore())
    await telegram_notifier.notify_new_ticket({"id": 1})
