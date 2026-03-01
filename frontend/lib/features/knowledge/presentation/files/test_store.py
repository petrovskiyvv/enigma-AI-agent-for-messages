"""
Юнит-тесты: app/core/store.py — класс JsonTicketStore

Ключевой момент: JsonTicketStore пишет данные в файл при каждой операции.
Поэтому тесты используют фикстуру tmp_store (из conftest.py), которая
создаёт файл в tmp_path pytest — изолированно, без влияния на production.

Покрытие:
  __init__    — файл не существует (defaults) / файл существует (_load)
  _save/_load — round-trip данных
  add         — id, created_at, инкремент, персистенция
  get_by_id   — существующий / несуществующий
  get_all     — без фильтров / status / tone / category / search / комбинация
  update      — поле / несколько полей / None не применяется / несуществующий
  stats       — пустое хранилище / счётчики by_tone/by_category/by_status / total
"""

import json
import pytest
from app.core.store import JsonTicketStore


# ──────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────

def make_ticket(**kwargs) -> dict:
    base = {
        "full_name": "Тестов Тест", "facility": "Завод",
        "phone": "+7 (000) 000-00-00", "email": "t@t.ru",
        "device_numbers": "TST-001", "device_type": "Прибор",
        "original_text": "Текст", "emotional_tone": "Нейтраль",
        "category": "Общий вопрос", "issue_summary": "Описание",
        "ai_response": "Ответ", "status": "Новое",
    }
    base.update(kwargs)
    return base


# ═══════════════════════════════════════════
# __init__ / persistence bootstrap
# ═══════════════════════════════════════════

class TestInit:
    def test_new_file_gets_default_tickets(self, tmp_path):
        """При отсутствии файла store создаёт 3 начальных тикета."""
        store = JsonTicketStore(path=str(tmp_path / "new.json"))
        assert len(store._tickets) == 3

    def test_new_file_created_on_disk(self, tmp_path):
        path = tmp_path / "new.json"
        JsonTicketStore(path=str(path))
        assert path.exists()

    def test_existing_file_loaded(self, tmp_path):
        """Если файл существует — данные загружаются из него, defaults не добавляются."""
        path = tmp_path / "existing.json"
        payload = {"tickets": [{"id": 99, "full_name": "Загруженный"}]}
        path.write_text(json.dumps(payload), encoding="utf-8")

        store = JsonTicketStore(path=str(path))
        assert len(store._tickets) == 1
        assert store._tickets[0]["full_name"] == "Загруженный"

    def test_next_id_recalculated_from_file(self, tmp_path):
        path = tmp_path / "ids.json"
        payload = {"tickets": [{"id": 10}, {"id": 20}]}
        path.write_text(json.dumps(payload), encoding="utf-8")

        store = JsonTicketStore(path=str(path))
        assert store._next_id == 21


# ═══════════════════════════════════════════
# _save / _load round-trip
# ═══════════════════════════════════════════

class TestSaveLoad:
    def test_data_persists_between_instances(self, tmp_path):
        path = str(tmp_path / "persist.json")
        s1 = JsonTicketStore(path=path)
        s1._tickets = []
        s1._next_id = 1
        s1._save()

        s1.add(make_ticket(full_name="Сохранённый"))

        # Второй экземпляр загружает тот же файл
        s2 = JsonTicketStore(path=path)
        assert len(s2._tickets) == 1
        assert s2._tickets[0]["full_name"] == "Сохранённый"

    def test_save_uses_tmp_then_replace(self, tmp_path):
        """После save tmp-файл должен быть удалён."""
        path = tmp_path / "t.json"
        store = JsonTicketStore(path=str(path))
        store._tickets = []
        store._save()
        tmp = path.with_suffix(path.suffix + ".tmp")
        assert not tmp.exists()

    def test_json_is_valid_utf8(self, tmp_store, tmp_path):
        tmp_store.add(make_ticket(full_name="Кириллица"))
        raw = tmp_store._path.read_text(encoding="utf-8")
        data = json.loads(raw)
        assert any(t.get("full_name") == "Кириллица" for t in data["tickets"])


# ═══════════════════════════════════════════
# add
# ═══════════════════════════════════════════

class TestAdd:
    def test_returns_ticket_with_id(self, tmp_store):
        t = tmp_store.add(make_ticket())
        assert t["id"] == 1

    def test_id_auto_increments(self, tmp_store):
        t1 = tmp_store.add(make_ticket())
        t2 = tmp_store.add(make_ticket())
        assert t2["id"] == t1["id"] + 1

    def test_created_at_set(self, tmp_store):
        t = tmp_store.add(make_ticket())
        assert "created_at" in t and t["created_at"]

    def test_ticket_stored_in_memory(self, tmp_store):
        tmp_store.add(make_ticket())
        assert len(tmp_store._tickets) == 1

    def test_fields_preserved(self, tmp_store):
        t = tmp_store.add(make_ticket(full_name="Особый"))
        assert t["full_name"] == "Особый"

    def test_original_dict_not_mutated(self, tmp_store):
        original = make_ticket()
        tmp_store.add(original)
        assert "id" not in original  # add работает с копией

    def test_saved_to_disk(self, tmp_store):
        tmp_store.add(make_ticket(full_name="Диск"))
        raw = json.loads(tmp_store._path.read_text(encoding="utf-8"))
        assert any(t.get("full_name") == "Диск" for t in raw["tickets"])


# ═══════════════════════════════════════════
# get_by_id
# ═══════════════════════════════════════════

class TestGetById:
    def test_returns_existing(self, tmp_store):
        added = tmp_store.add(make_ticket())
        found = tmp_store.get_by_id(added["id"])
        assert found is not None
        assert found["id"] == added["id"]

    def test_returns_none_for_missing(self, tmp_store):
        assert tmp_store.get_by_id(9999) is None

    def test_correct_ticket_from_multiple(self, tmp_store):
        t1 = tmp_store.add(make_ticket(full_name="Первый"))
        t2 = tmp_store.add(make_ticket(full_name="Второй"))
        assert tmp_store.get_by_id(t1["id"])["full_name"] == "Первый"
        assert tmp_store.get_by_id(t2["id"])["full_name"] == "Второй"


# ═══════════════════════════════════════════
# get_all + filters
# ═══════════════════════════════════════════

class TestGetAll:
    def test_returns_all_without_filters(self, store_with_data):
        assert len(store_with_data.get_all()) == 3

    def test_empty_store(self, tmp_store):
        assert tmp_store.get_all() == []

    def test_filter_by_status(self, store_with_data):
        result = store_with_data.get_all(status="Новое")
        assert all(t["status"] == "Новое" for t in result)
        assert len(result) == 1

    def test_filter_by_tone(self, store_with_data):
        result = store_with_data.get_all(tone="Негатив")
        assert len(result) == 1
        assert result[0]["emotional_tone"] == "Негатив"

    def test_filter_by_category(self, store_with_data):
        result = store_with_data.get_all(category="Документация")
        assert len(result) == 1
        assert result[0]["category"] == "Документация"

    def test_search_by_full_name(self, store_with_data):
        result = store_with_data.get_all(search="петрова")
        assert len(result) == 1
        assert "Петрова" in result[0]["full_name"]

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

    def test_does_not_mutate_internal_list(self, tmp_store):
        tmp_store.add(make_ticket())
        result = tmp_store.get_all()
        result.clear()
        assert len(tmp_store._tickets) == 1


# ═══════════════════════════════════════════
# update
# ═══════════════════════════════════════════

class TestUpdate:
    def test_update_single_field(self, tmp_store):
        t = tmp_store.add(make_ticket(status="Новое"))
        updated = tmp_store.update(t["id"], {"status": "В работе"})
        assert updated["status"] == "В работе"

    def test_update_multiple_fields(self, tmp_store):
        t = tmp_store.add(make_ticket())
        tmp_store.update(t["id"], {"status": "Закрыто", "ai_response": "Готово"})
        result = tmp_store.get_by_id(t["id"])
        assert result["status"] == "Закрыто"
        assert result["ai_response"] == "Готово"

    def test_none_value_not_applied(self, tmp_store):
        t = tmp_store.add(make_ticket(status="Новое"))
        tmp_store.update(t["id"], {"status": None})
        assert tmp_store.get_by_id(t["id"])["status"] == "Новое"

    def test_other_fields_preserved(self, tmp_store):
        t = tmp_store.add(make_ticket(full_name="Иванов", status="Новое"))
        tmp_store.update(t["id"], {"status": "Закрыто"})
        assert tmp_store.get_by_id(t["id"])["full_name"] == "Иванов"

    def test_nonexistent_returns_none(self, tmp_store):
        assert tmp_store.update(9999, {"status": "Закрыто"}) is None

    def test_update_persisted_to_disk(self, tmp_store):
        t = tmp_store.add(make_ticket(status="Новое"))
        tmp_store.update(t["id"], {"status": "Закрыто"})
        raw = json.loads(tmp_store._path.read_text(encoding="utf-8"))
        disk_ticket = next(x for x in raw["tickets"] if x["id"] == t["id"])
        assert disk_ticket["status"] == "Закрыто"


# ═══════════════════════════════════════════
# stats
# ═══════════════════════════════════════════

class TestStats:
    def test_empty_store(self, tmp_store):
        s = tmp_store.stats()
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

    def test_accumulates_correctly(self, tmp_store):
        tmp_store.add(make_ticket(emotional_tone="Негатив", status="Новое", category="Калибровка"))
        tmp_store.add(make_ticket(emotional_tone="Негатив", status="Новое", category="Калибровка"))
        s = tmp_store.stats()
        assert s["by_tone"]["Негатив"] == 2
        assert s["by_status"]["Новое"] == 2
