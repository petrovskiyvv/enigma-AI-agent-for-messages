"""Unit tests for DB-backed ticket store (app/core/store.py).

These tests used to validate JsonTicketStore. The implementation is now
SQLAlchemy/Postgres, so we validate the same behavior via DbTicketStore.
"""

from __future__ import annotations

from datetime import datetime, timezone


def make_ticket(**kwargs) -> dict:
    base = {
        "full_name": "Тестов Тест",
        "facility": "Завод",
        "phone": "+7 (000) 000-00-00",
        "email": "t@t.ru",
        "device_numbers": "TST-001",
        "device_type": "Прибор",
        "original_text": "Текст",
        "emotional_tone": "Нейтраль",
        "category": "Общий вопрос",
        "issue_summary": "Описание",
        "ai_response": "Ответ",
        "status": "Новое",
    }
    base.update(kwargs)
    return base


class TestAdd:
    def test_returns_ticket_with_id(self, ticket_store):
        t = ticket_store.add(make_ticket())
        assert isinstance(t["id"], int)
        assert t["id"] > 0

    def test_id_auto_increments(self, ticket_store):
        t1 = ticket_store.add(make_ticket())
        t2 = ticket_store.add(make_ticket())
        assert t2["id"] == t1["id"] + 1

    def test_created_at_set_and_isoformat(self, ticket_store):
        t = ticket_store.add(make_ticket())
        dt = datetime.fromisoformat(t["created_at"])
        assert dt

    def test_original_dict_not_mutated(self, ticket_store):
        original = make_ticket()
        ticket_store.add(original)
        assert "id" not in original

    def test_accepts_explicit_created_at(self, ticket_store):
        dt = datetime(2030, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        t = ticket_store.add(make_ticket(created_at=dt))
        assert t["created_at"].startswith("2030-01-01")


class TestGetById:
    def test_returns_existing(self, ticket_store):
        added = ticket_store.add(make_ticket())
        found = ticket_store.get_by_id(added["id"])
        assert found is not None
        assert found["id"] == added["id"]

    def test_returns_none_for_missing(self, ticket_store):
        assert ticket_store.get_by_id(9999) is None

    def test_correct_ticket_from_multiple(self, ticket_store):
        t1 = ticket_store.add(make_ticket(full_name="Первый"))
        t2 = ticket_store.add(make_ticket(full_name="Второй"))
        assert ticket_store.get_by_id(t1["id"])["full_name"] == "Первый"
        assert ticket_store.get_by_id(t2["id"])["full_name"] == "Второй"


class TestGetAll:
    def test_returns_all_without_filters(self, store_with_data):
        assert len(store_with_data.get_all()) == 3

    def test_empty_store(self, ticket_store):
        assert ticket_store.get_all() == []

    def test_filter_by_status(self, store_with_data):
        result = store_with_data.get_all(status="Новое")
        assert len(result) == 1
        assert all(t["status"] == "Новое" for t in result)

    def test_filter_by_tone(self, store_with_data):
        result = store_with_data.get_all(tone="Негатив")
        assert len(result) == 1
        assert result[0]["emotional_tone"] == "Негатив"

    def test_filter_by_category(self, store_with_data):
        result = store_with_data.get_all(category="Документация")
        assert len(result) == 1
        assert result[0]["category"] == "Документация"

    def test_search_case_insensitive(self, store_with_data):
        # SQLite doesn't case-fold Cyrillic reliably; store test data is lowercase.
        result = store_with_data.get_all(search="петрова")
        assert len(result) == 1
        assert "петрова" in result[0]["full_name"]

    def test_search_by_facility(self, store_with_data):
        result = store_with_data.get_all(search="нефтехим")
        assert len(result) == 1

    def test_search_by_device_numbers(self, store_with_data):
        result = store_with_data.get_all(search="нк-001")
        assert len(result) == 1

    def test_search_by_issue_summary(self, store_with_data):
        result = store_with_data.get_all(search="документ")
        assert len(result) == 1

    def test_combined_filters(self, store_with_data):
        result = store_with_data.get_all(status="Новое", category="Неисправность")
        assert len(result) == 1

    def test_no_match_returns_empty(self, store_with_data):
        assert store_with_data.get_all(status="НесуществующийСтатус") == []


class TestUpdateDelete:
    def test_update_single_field(self, ticket_store):
        t = ticket_store.add(make_ticket(status="Новое"))
        updated = ticket_store.update(t["id"], {"status": "В работе"})
        assert updated["status"] == "В работе"

    def test_update_multiple_fields(self, ticket_store):
        t = ticket_store.add(make_ticket())
        ticket_store.update(t["id"], {"status": "Закрыто", "ai_response": "Готово"})
        result = ticket_store.get_by_id(t["id"])
        assert result["status"] == "Закрыто"
        assert result["ai_response"] == "Готово"

    def test_none_value_not_applied(self, ticket_store):
        t = ticket_store.add(make_ticket(status="Новое"))
        ticket_store.update(t["id"], {"status": None})
        assert ticket_store.get_by_id(t["id"])["status"] == "Новое"

    def test_nonexistent_returns_none(self, ticket_store):
        assert ticket_store.update(9999, {"status": "Закрыто"}) is None

    def test_delete_existing_and_missing(self, ticket_store):
        t = ticket_store.add(make_ticket())
        assert ticket_store.delete(t["id"]) is True
        assert ticket_store.get_by_id(t["id"]) is None
        assert ticket_store.delete(t["id"]) is False


class TestStats:
    def test_empty_store(self, ticket_store):
        s = ticket_store.stats()
        assert s["total"] == 0
        assert s["by_tone"] == {}
        assert s["by_category"] == {}
        assert s["by_status"] == {}

    def test_total_count(self, store_with_data):
        assert store_with_data.stats()["total"] == 3

    def test_by_tone_counts(self, store_with_data):
        s = store_with_data.stats()
        assert s["by_tone"]["Негатив"] == 1
        assert s["by_tone"]["Нейтраль"] == 1
        assert s["by_tone"]["Позитив"] == 1

    def test_by_category_counts(self, store_with_data):
        s = store_with_data.stats()
        assert s["by_category"]["Неисправность"] == 1
        assert s["by_category"]["Документация"] == 1
        assert s["by_category"]["Калибровка"] == 1

    def test_by_status_counts(self, store_with_data):
        s = store_with_data.stats()
        assert s["by_status"]["Новое"] == 1
        assert s["by_status"]["В работе"] == 1
        assert s["by_status"]["Закрыто"] == 1

    def test_accumulates_correctly(self, ticket_store):
        ticket_store.add(make_ticket(emotional_tone="Негатив", status="Новое", category="Калибровка"))
        ticket_store.add(make_ticket(emotional_tone="Негатив", status="Новое", category="Калибровка"))
        s = ticket_store.stats()
        assert s["by_tone"]["Негатив"] == 2
        assert s["by_status"]["Новое"] == 2
