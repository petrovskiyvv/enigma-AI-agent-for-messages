from __future__ import annotations


def test_upsert_get_list_all(ticket_store):
    from app.core.telegram_ticket_store import DbTelegramTicketStore

    # Telegram bindings are FK'ed to tickets, so create tickets first
    t1 = ticket_store.add({"full_name": "A", "emotional_tone": "Нейтраль", "status": "Новое"})
    t2 = ticket_store.add({"full_name": "B", "emotional_tone": "Нейтраль", "status": "Новое"})

    ts = DbTelegramTicketStore()
    ts.upsert_ticket(str(t1["id"]), {"created_at": "2025-01-01T00:00:00Z", "assignee": None})
    ts.upsert_ticket(str(t2["id"]), {"created_at": "2025-01-02T00:00:00Z", "assignee": "@a"})

    assert ts.get(str(t1["id"]))["ticket_id"] == str(t1["id"])
    assert ts.get(str(t2["id"]))["assignee"] == "@a"

    all_t = {t["ticket_id"] for t in ts.list_all()}
    assert all_t == {str(t1["id"]), str(t2["id"])}


def test_add_event_orders_and_missing_ticket_is_isolated(ticket_store):
    from app.core.telegram_ticket_store import DbTelegramTicketStore

    t1 = ticket_store.add({"full_name": "A", "emotional_tone": "Нейтраль", "status": "Новое"})
    ts = DbTelegramTicketStore()
    ts.upsert_ticket(str(t1["id"]), {"created_at": "2025-01-01", "assignee": None})

    # Events should be ordered by ts
    ts.add_event(str(t1["id"]), {"ts": "2025-01-02T00:00:00Z", "type": "taken", "by": "@u"})
    ts.add_event(str(t1["id"]), {"ts": "2025-01-01T00:00:00Z", "type": "created", "by": None})

    t = ts.get(str(t1["id"]))
    assert [e["type"] for e in t["events"]] == ["created", "taken"]

    # Missing ticket id should not appear (no implicit create)
    assert ts.get("99999") is None
