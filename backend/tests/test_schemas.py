"""
Юнит-тесты: app/schemas/ticket.py

Покрытие:
  TicketCreate   — дефолты / все поля / лишние поля игнорируются
  TicketUpdate   — все None по умолчанию / частичное заполнение / dict(exclude_none)
  AnalyzeRequest — обязательный text / пустая строка
  StatsResponse  — корректная структура / типы полей
"""

import pytest
from pydantic import ValidationError

from app.schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    AnalyzeRequest,
    StatsResponse,
)


# ═══════════════════════════════════════════
# TicketCreate
# ═══════════════════════════════════════════

class TestTicketCreate:
    def test_all_fields_empty_by_default(self):
        t = TicketCreate()
        assert t.full_name == ""
        assert t.facility == ""
        assert t.phone == ""
        assert t.email == ""
        assert t.device_numbers == ""
        assert t.device_type == ""
        assert t.original_text == ""

    def test_all_fields_set(self):
        t = TicketCreate(
            full_name="Иванов Иван",
            facility="Завод №1",
            phone="+7 (999) 000-00-00",
            email="ivan@test.ru",
            device_numbers="НК-001",
            device_type="Газоанализатор",
            original_text="Текст обращения",
        )
        assert t.full_name == "Иванов Иван"
        assert t.email == "ivan@test.ru"
        assert t.original_text == "Текст обращения"

    def test_partial_fields(self):
        t = TicketCreate(full_name="Только имя")
        assert t.full_name == "Только имя"
        assert t.email == ""

    def test_instantiation_from_dict(self):
        data = {"full_name": "Тест", "email": "t@t.ru"}
        t = TicketCreate(**data)
        assert t.full_name == "Тест"


# ═══════════════════════════════════════════
# TicketUpdate
# ═══════════════════════════════════════════

class TestTicketUpdate:
    def test_all_none_by_default(self):
        u = TicketUpdate()
        assert u.status is None
        assert u.ai_response is None
        assert u.full_name is None
        assert u.facility is None
        assert u.phone is None
        assert u.email is None
        assert u.device_numbers is None
        assert u.device_type is None
        assert u.issue_summary is None

    def test_partial_update(self):
        u = TicketUpdate(status="В работе", ai_response="Ответ")
        assert u.status == "В работе"
        assert u.ai_response == "Ответ"
        assert u.full_name is None

    def test_dict_exclude_none(self):
        """Метод, который использует TicketService при обновлении."""
        u = TicketUpdate(status="Закрыто")
        d = u.dict(exclude_none=True)
        assert d == {"status": "Закрыто"}
        assert "ai_response" not in d

    def test_all_fields_set(self):
        u = TicketUpdate(
            status="Закрыто",
            ai_response="Ответ",
            full_name="Новое имя",
            facility="Завод",
            phone="111",
            email="new@test.ru",
            device_numbers="X-001",
            device_type="Датчик",
            issue_summary="Краткое",
        )
        d = u.dict(exclude_none=True)
        assert len(d) == 9

    def test_dict_exclude_none_empty_gives_empty_dict(self):
        assert TicketUpdate().dict(exclude_none=True) == {}


# ═══════════════════════════════════════════
# AnalyzeRequest
# ═══════════════════════════════════════════

class TestAnalyzeRequest:
    def test_text_required(self):
        with pytest.raises(ValidationError):
            AnalyzeRequest()  # type: ignore

    def test_valid_text(self):
        r = AnalyzeRequest(text="Прибор не работает")
        assert r.text == "Прибор не работает"

    def test_empty_string_allowed(self):
        r = AnalyzeRequest(text="")
        assert r.text == ""

    def test_multiline_text(self):
        text = "Строка 1\nСтрока 2"
        r = AnalyzeRequest(text=text)
        assert r.text == text


# ═══════════════════════════════════════════
# StatsResponse
# ═══════════════════════════════════════════

class TestStatsResponse:
    def test_valid_stats(self):
        s = StatsResponse(
            total=3,
            by_tone={"Негатив": 1, "Нейтрально": 2},
            by_category={"Калибровка": 1},
            by_status={"Новое": 3},
        )
        assert s.total == 3
        assert s.by_tone["Негатив"] == 1

    def test_empty_dicts(self):
        s = StatsResponse(total=0, by_tone={}, by_category={}, by_status={})
        assert s.total == 0

    def test_total_required(self):
        with pytest.raises(ValidationError):
            StatsResponse(by_tone={}, by_category={}, by_status={})  # type: ignore

    def test_by_tone_required(self):
        with pytest.raises(ValidationError):
            StatsResponse(total=0, by_category={}, by_status={})  # type: ignore
