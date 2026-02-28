from __future__ import annotations

import types

import pytest


def test_extract_text_from_message_and_channel_post():
    from app.bot import bot_service

    upd_msg = {
        "message": {
            "chat": {"id": 1, "title": "T", "type": "group"},
            "text": "hello",
        }
    }
    assert bot_service._extract_text(upd_msg) == (1, "hello", "T", "group")

    upd_post = {
        "channel_post": {
            "chat": {"id": 2, "username": "chan", "type": "channel"},
            "caption": "cap",
        }
    }
    assert bot_service._extract_text(upd_post) == (2, "cap", "chan", "channel")

    assert bot_service._extract_text({}) == (None, None, None, None)


def test_timeline_keyboard_variants():
    from app.bot import bot_service

    kb_free = bot_service._timeline_keyboard("t1", assignee=None)
    assert kb_free["inline_keyboard"][0][0]["callback_data"] == "take:t1"

    kb_taken_by_me = bot_service._timeline_keyboard("t1", assignee="@me", actor="@me")
    assert "decline:t1" in kb_taken_by_me["inline_keyboard"][0][0]["callback_data"]

    kb_taken_other = bot_service._timeline_keyboard("t1", assignee="@other", actor="@me")
    assert kb_taken_other["inline_keyboard"][0][0]["callback_data"] == "take:t1"


def test_match_ticket_for_auto_forward(monkeypatch):
    from app.bot import bot_service

    class DummyTS:
        def list_all(self):
            return [
                {
                    "ticket_id": "t1",
                    "discussion_chat_id": -100,
                    "channel_chat_id": -200,
                    "channel_message_id": 10,
                }
            ]

    monkeypatch.setattr(bot_service, "ticket_store", DummyTS())

    msg = {
        "is_automatic_forward": True,
        "chat": {"id": -100},
        "forward_from_chat": {"id": -200},
        "forward_from_message_id": 10,
    }
    assert bot_service._match_ticket_for_auto_forward(msg) == "t1"

    msg_bad = {"is_automatic_forward": False}
    assert bot_service._match_ticket_for_auto_forward(msg_bad) is None


@pytest.mark.asyncio
async def test_tg_call_ok_and_not_ok():
    from app.bot import bot_service

    class Resp:
        def __init__(self, ok: bool):
            self._ok = ok

        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": self._ok, "result": {"x": 1}}

    class DummyClient:
        def __init__(self, ok: bool):
            self.ok = ok
            self.last = None

        async def post(self, url, json):
            self.last = (url, json)
            return Resp(self.ok)

    c1 = DummyClient(True)
    r = await bot_service._tg_call(c1, "sendMessage", {"a": 1})
    assert r == {"x": 1}
    assert "sendMessage" in c1.last[0]

    c2 = DummyClient(False)
    r2 = await bot_service._tg_call(c2, "sendMessage", {"a": 1})
    assert r2 is None


@pytest.mark.asyncio
async def test_handle_action_callback_take_and_decline(tmp_path, monkeypatch):
    from app.bot import bot_service
    from app.core.telegram_ticket_store import JsonTelegramTicketStore

    ts = JsonTelegramTicketStore(path=str(tmp_path / "tickets.json"))
    monkeypatch.setattr(bot_service, "ticket_store", ts)

    monkeypatch.setattr(bot_service, "_utc_now_iso", lambda: "2030-01-01T00:00:00+00:00")

    ts.upsert_ticket(
        "t1",
        {
            "base_text": "BASE",
            "channel_chat_id": -10,
            "channel_message_id": 1,
            "discussion_chat_id": -11,
            "timeline_message_id": 2,
            "assignee": None,
            "events": [],
        },
    )

    calls: list[tuple[str, dict]] = []

    async def fake_tg_call(_client, method: str, payload: dict):
        calls.append((method, payload))
        return {"message_id": 999}

    monkeypatch.setattr(bot_service, "_tg_call", fake_tg_call)

    upd_take = {
        "callback_query": {
            "id": "cq1",
            "data": "take:t1",
            "from": {"username": "alice"},
        }
    }
    await bot_service._handle_action_callback(types.SimpleNamespace(), upd_take)
    t = ts.get("t1")
    assert t["assignee"] == "@alice"
    assert any(e["type"] == "taken" for e in t["events"])
    assert any(m == "editMessageText" for m, _ in calls)
    assert any(m == "answerCallbackQuery" for m, _ in calls)

    calls.clear()

    await bot_service._handle_action_callback(types.SimpleNamespace(), upd_take)
    assert any(m == "answerCallbackQuery" and "У вас уже" in p.get("text", "") for m, p in calls)

    calls.clear()

    upd_take_bob = {
        "callback_query": {
            "id": "cq2",
            "data": "take:t1",
            "from": {"username": "bob"},
        }
    }
    await bot_service._handle_action_callback(types.SimpleNamespace(), upd_take_bob)
    t2 = ts.get("t1")
    assert t2["assignee"] == "@bob"
    assert any(e["type"] == "retaken" for e in t2["events"])

    calls.clear()

    upd_decl_forbidden = {
        "callback_query": {
            "id": "cq3",
            "data": "decline:t1",
            "from": {"username": "alice"},
        }
    }
    await bot_service._handle_action_callback(types.SimpleNamespace(), upd_decl_forbidden)
    assert any(m == "answerCallbackQuery" and "только текущий" in p.get("text", "") for m, p in calls)

    calls.clear()

    upd_decl = {
        "callback_query": {
            "id": "cq4",
            "data": "decline:t1",
            "from": {"username": "bob"},
        }
    }
    await bot_service._handle_action_callback(types.SimpleNamespace(), upd_decl)
    t3 = ts.get("t1")
    assert t3["assignee"] is None
    assert any(e["type"] == "released" for e in t3["events"])


@pytest.mark.asyncio
async def test_handle_discussion_auto_forward_send_and_edit(tmp_path, monkeypatch):
    from app.bot import bot_service
    from app.core.telegram_ticket_store import JsonTelegramTicketStore

    ts = JsonTelegramTicketStore(path=str(tmp_path / "tickets.json"))
    monkeypatch.setattr(bot_service, "ticket_store", ts)

    ts.upsert_ticket(
        "t1",
        {
            "created_at": "2030-01-01",
            "discussion_chat_id": -100,
            "channel_chat_id": -200,
            "channel_message_id": 10,
            "assignee": None,
            "events": [],
        },
    )

    calls: list[tuple[str, dict]] = []

    async def fake_tg_call(_client, method: str, payload: dict):
        calls.append((method, payload))
        if method == "sendMessage":
            return {"message_id": 777}
        return {"ok": True}

    monkeypatch.setattr(bot_service, "_tg_call", fake_tg_call)

    upd = {
        "message": {
            "message_id": 55,
            "is_automatic_forward": True,
            "chat": {"id": -100},
            "forward_from_chat": {"id": -200},
            "forward_from_message_id": 10,
        }
    }

    await bot_service._handle_discussion_auto_forward(types.SimpleNamespace(), upd)
    t = ts.get("t1")
    assert t["discussion_root_message_id"] == 55
    assert t["timeline_message_id"] == 777
    assert any(m == "sendMessage" for m, _ in calls)

    calls.clear()

    await bot_service._handle_discussion_auto_forward(types.SimpleNamespace(), upd)
    assert any(m == "editMessageText" for m, _ in calls)
