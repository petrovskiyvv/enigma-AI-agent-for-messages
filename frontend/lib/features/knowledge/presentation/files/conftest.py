"""
Общие фикстуры для всего тестового套件.

Ключевые решения:
- JsonTicketStore тестируется через tmp_path (tmpdir pytest) — файл создаётся
  во временной директории и удаляется после теста автоматически.
- FastAPI TestClient поднимается с подменённым store через monkeypatch,
  чтобы интеграционные тесты не трогали production-файл tickets.json.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.store import JsonTicketStore
from app.main import create_app


# ──────────────────────────────────────────────────────────────
# Store fixture — изолированное хранилище в tmp-файле
# ──────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_store(tmp_path):
    """
    Чистый JsonTicketStore без начальных данных.
    Файл создаётся в изолированной временной директории pytest.
    """
    store = JsonTicketStore(path=str(tmp_path / "tickets_test.json"))
    # Сбрасываем дефолтные тикеты, которые вставляет __init__
    store._tickets = []
    store._next_id = 1
    store._save()
    return store


@pytest.fixture
def store_with_data(tmp_store):
    """Store с тремя предзаполненными тикетами для тестов фильтрации/статистики."""
    tmp_store.add({
        "full_name": "Иванов Иван", "facility": "Завод Казань",
        "phone": "+7 (999) 111-11-11", "email": "ivan@test.ru",
        "device_numbers": "НК-001", "device_type": "Тип А",
        "original_text": "Прибор не работает срочно!",
        "emotional_tone": "Негатив", "category": "Неисправность",
        "issue_summary": "Авария оборудования", "ai_response": "Ответ", "status": "Новое",
    })
    tmp_store.add({
        "full_name": "Петрова Светлана", "facility": "ООО ГазСнаб",
        "phone": "+7 (347) 222-22-22", "email": "petra@test.ru",
        "device_numbers": "А-2241", "device_type": "Тип Б",
        "original_text": "Нужен паспорт на прибор.",
        "emotional_tone": "Нейтраль", "category": "Документация",
        "issue_summary": "Запрос документов", "ai_response": "Ответ", "status": "В работе",
    })
    tmp_store.add({
        "full_name": "Смирнов Алексей", "facility": "АО НефтеХим",
        "phone": "+7 (855) 333-33-33", "email": "smir@test.ru",
        "device_numbers": "НК-002", "device_type": "Тип В",
        "original_text": "Спасибо за помощь с калибровкой!",
        "emotional_tone": "Позитив", "category": "Калибровка",
        "issue_summary": "Калибровка выполнена", "ai_response": "Ответ", "status": "Закрыто",
    })
    return tmp_store


# ──────────────────────────────────────────────────────────────
# HTTP-клиент для интеграционных тестов
# ──────────────────────────────────────────────────────────────

@pytest.fixture
def client(tmp_store, monkeypatch):
    """
    TestClient с подменой глобального ticket_store на изолированный tmp_store.
    Патчим во всех модулях, которые импортировали store напрямую.
    """
    import app.core.store as store_module
    import app.services.ticket_service as svc_module

    monkeypatch.setattr(store_module, "ticket_store", tmp_store)
    monkeypatch.setattr(svc_module, "ticket_store", tmp_store)

    application = create_app()
    with TestClient(application) as c:
        yield c


@pytest.fixture
def client_with_data(store_with_data, monkeypatch):
    """TestClient с тремя предзаполненными тикетами."""
    import app.core.store as store_module
    import app.services.ticket_service as svc_module

    monkeypatch.setattr(store_module, "ticket_store", store_with_data)
    monkeypatch.setattr(svc_module, "ticket_store", store_with_data)

    application = create_app()
    with TestClient(application) as c:
        yield c
