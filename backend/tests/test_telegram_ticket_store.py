import json

import pytest


@pytest.fixture
def tmp_ticket_store(tmp_path):
    from app.core.telegram_ticket_store import JsonTelegramTicketStore

    return JsonTelegramTicketStore(path=str(tmp_path / "telegram_tickets_test.json"))


def test_upsert_get_list_all(tmp_ticket_store):
    tmp_ticket_store.upsert_ticket("t1", {"created_at": "2025-01-01T00:00:00Z", "assignee": None})
    tmp_ticket_store.upsert_ticket("t2", {"created_at": "2025-01-02T00:00:00Z", "assignee": "@a"})

    assert tmp_ticket_store.get("t1")["ticket_id"] == "t1"
    assert tmp_ticket_store.get("t2")["assignee"] == "@a"

    all_t = {t["ticket_id"] for t in tmp_ticket_store.list_all()}
    assert all_t == {"t1", "t2"}

    raw = json.loads(tmp_ticket_store._path.read_text(encoding="utf-8"))
    assert "tickets" in raw and "t1" in raw["tickets"]


def test_add_event_appends_and_is_noop_for_missing_ticket(tmp_ticket_store):
    tmp_ticket_store.add_event("missing", {"ts": "x", "type": "created", "by": None})
    assert tmp_ticket_store.get("missing") is None

    tmp_ticket_store.upsert_ticket("t1", {"events": []})
    tmp_ticket_store.add_event("t1", {"ts": "2025-01-01", "type": "created", "by": None})
    tmp_ticket_store.add_event("t1", {"ts": "2025-01-01", "type": "taken", "by": "@u"})

    t = tmp_ticket_store.get("t1")
    assert [e["type"] for e in t["events"]] == ["created", "taken"]
