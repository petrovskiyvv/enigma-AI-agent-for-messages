"""
Юнит-тесты: app/services/ticket_service.py — класс TicketService

Используем monkeypatch для подмены глобального ticket_store внутри модуля,
чтобы сервис работал с изолированным tmp_store, а не с production-файлом.

Покрытие:
  get_list           — делегирование в store (фильтры прокидываются)
  get_one            — существующий / несуществующий
  create             — с текстом (анализ) / без текста (defaults) / поля сохраняются
  update             — существующий / несуществующий (None)
  analyze_and_create — извлечение полей из текста / создание тикета
  get_stats          — делегирование в store.stats()
"""

import pytest
from app.services.ticket_service import TicketService
from app.schemas.ticket import TicketCreate, TicketUpdate


@pytest.fixture
def service(tmp_store, monkeypatch):
    import app.services.ticket_service as svc_module
    monkeypatch.setattr(svc_module, "ticket_store", tmp_store)
    return TicketService()


@pytest.fixture
def service_with_data(store_with_data, monkeypatch):
    import app.services.ticket_service as svc_module
    monkeypatch.setattr(svc_module, "ticket_store", store_with_data)
    return TicketService()


# ═══════════════════════════════════════════
# get_list
# ═══════════════════════════════════════════

class TestGetList:
    def test_returns_all(self, service_with_data):
        result = service_with_data.get_list()
        assert len(result) == 3

    def test_filter_by_status(self, service_with_data):
        result = service_with_data.get_list(status="Новое")
        assert all(t["status"] == "Новое" for t in result)

    def test_filter_by_tone(self, service_with_data):
        result = service_with_data.get_list(tone="Негатив")
        assert len(result) == 1

    def test_filter_by_category(self, service_with_data):
        result = service_with_data.get_list(category="Калибровка")
        assert len(result) == 1

    def test_search(self, service_with_data):
        result = service_with_data.get_list(search="петрова")
        assert len(result) == 1

    def test_empty_store(self, service):
        assert service.get_list() == []


# ═══════════════════════════════════════════
# get_one
# ═══════════════════════════════════════════

class TestGetOne:
    def test_existing_ticket(self, service_with_data):
        all_tickets = service_with_data.get_list()
        first_id = all_tickets[0]["id"]
        result = service_with_data.get_one(first_id)
        assert result is not None
        assert result["id"] == first_id

    def test_nonexistent_returns_none(self, service):
        assert service.get_one(9999) is None


# ═══════════════════════════════════════════
# create
# ═══════════════════════════════════════════

class TestCreate:
    def test_create_with_text_runs_analysis(self, service):
        data = TicketCreate(
            full_name="Иванов Иван",
            original_text="Прибор не работает, срочно!",
        )
        ticket = service.create(data)
        assert ticket["emotional_tone"] == "Негатив"
        assert ticket["category"] == "Неисправность"

    def test_create_without_text_uses_defaults(self, service):
        data = TicketCreate(full_name="Петров Пётр")
        ticket = service.create(data)
        assert ticket["emotional_tone"] == "Нейтраль"
        assert ticket["category"] == "Общий вопрос"
        assert ticket["issue_summary"] == ""
        assert ticket["ai_response"] == ""

    def test_create_preserves_user_fields(self, service):
        data = TicketCreate(
            full_name="Смирнов Алексей",
            facility="Завод Казань",
            phone="+7 (999) 000-00-00",
            email="s@test.ru",
            device_numbers="НК-001",
            device_type="Газоанализатор",
        )
        ticket = service.create(data)
        assert ticket["full_name"] == "Смирнов Алексей"
        assert ticket["facility"] == "Завод Казань"
        assert ticket["email"] == "s@test.ru"

    def test_create_sets_status_new(self, service):
        ticket = service.create(TicketCreate())
        assert ticket["status"] == "Новое"

    def test_create_generates_ai_response_when_text(self, service):
        data = TicketCreate(original_text="Нужен паспорт прибора.")
        ticket = service.create(data)
        assert ticket["ai_response"] != ""
        assert "ЭРИС" in ticket["ai_response"]

    def test_create_returns_ticket_with_id(self, service):
        ticket = service.create(TicketCreate())
        assert "id" in ticket
        assert isinstance(ticket["id"], int)


# ═══════════════════════════════════════════
# update
# ═══════════════════════════════════════════

class TestUpdate:
    def test_update_status(self, service_with_data):
        all_t = service_with_data.get_list()
        tid = all_t[0]["id"]
        result = service_with_data.update(tid, TicketUpdate(status="Закрыто"))
        assert result["status"] == "Закрыто"

    def test_update_ai_response(self, service_with_data):
        tid = service_with_data.get_list()[0]["id"]
        result = service_with_data.update(tid, TicketUpdate(ai_response="Новый ответ"))
        assert result["ai_response"] == "Новый ответ"

    def test_update_nonexistent_returns_none(self, service):
        assert service.update(9999, TicketUpdate(status="Закрыто")) is None

    def test_update_none_fields_not_overwritten(self, service_with_data):
        ticket = service_with_data.get_list()[0]
        tid = ticket["id"]
        original_name = ticket["full_name"]
        service_with_data.update(tid, TicketUpdate(status="В работе"))
        updated = service_with_data.get_one(tid)
        assert updated["full_name"] == original_name


# ═══════════════════════════════════════════
# analyze_and_create
# ═══════════════════════════════════════════

class TestAnalyzeAndCreate:
    SAMPLE_TEXT = (
        "Добрый день! Прибор не работает, индикатор мигает красным. "
        "Зав. номер: НК-001. "
        "Позвоните +7 (999) 123-45-67. "
        "С уважением, Иванов Иван Иванович"
    )

    def test_creates_ticket(self, service):
        ticket = service.analyze_and_create(self.SAMPLE_TEXT)
        assert "id" in ticket

    def test_extracts_phone(self, service):
        ticket = service.analyze_and_create(self.SAMPLE_TEXT)
        assert "999" in ticket["phone"]

    def test_extracts_name(self, service):
        ticket = service.analyze_and_create(self.SAMPLE_TEXT)
        assert "Иванов" in ticket["full_name"]

    def test_detects_negative_tone(self, service):
        ticket = service.analyze_and_create(self.SAMPLE_TEXT)
        assert ticket["emotional_tone"] == "Негатив"

    def test_detects_malfunction_category(self, service):
        ticket = service.analyze_and_create(self.SAMPLE_TEXT)
        assert ticket["category"] == "Неисправность"

    def test_status_is_new(self, service):
        ticket = service.analyze_and_create(self.SAMPLE_TEXT)
        assert ticket["status"] == "Новое"

    def test_generates_ai_response(self, service):
        ticket = service.analyze_and_create(self.SAMPLE_TEXT)
        assert ticket["ai_response"] != ""

    def test_original_text_saved(self, service):
        ticket = service.analyze_and_create(self.SAMPLE_TEXT)
        assert ticket["original_text"] == self.SAMPLE_TEXT


# ═══════════════════════════════════════════
# get_stats
# ═══════════════════════════════════════════

class TestGetStats:
    def test_returns_stats_dict(self, service_with_data):
        stats = service_with_data.get_stats()
        assert "total" in stats
        assert "by_tone" in stats
        assert "by_category" in stats
        assert "by_status" in stats

    def test_total_matches_ticket_count(self, service_with_data):
        assert service_with_data.get_stats()["total"] == 3

    def test_empty_store_stats(self, service):
        stats = service.get_stats()
        assert stats["total"] == 0
