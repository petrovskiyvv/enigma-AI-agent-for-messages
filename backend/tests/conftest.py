"""pytest fixtures.

All tests run against an isolated SQLite DB (file-based) to be CI-friendly.
The application code uses global SessionLocal objects imported into modules,
so we patch SessionLocal in app.core.db and in the modules that imported it.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def db_engine(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("db") / "test.sqlite"
    engine = create_engine(
        f"sqlite+pysqlite:///{db_file}",
        connect_args={"check_same_thread": False},
        future=True,
    )

    # Enforce FKs in SQLite so tests match Postgres semantics.
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


@pytest.fixture(scope="session")
def db_session_factory(db_engine):
    return sessionmaker(bind=db_engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture(autouse=True)
def _patch_db(monkeypatch, db_engine, db_session_factory):
    """Patch SessionLocal/engine everywhere and recreate schema for each test."""
    from app.core import db as db_module
    from app.core.models import Base

    # Patch core db module
    monkeypatch.setattr(db_module, "engine", db_engine)
    monkeypatch.setattr(db_module, "SessionLocal", db_session_factory)

    # Patch modules that imported SessionLocal directly
    import app.core.store as store_module
    import app.core.telegram_store as tg_store_module
    import app.core.telegram_ticket_store as tg_ticket_module

    monkeypatch.setattr(store_module, "SessionLocal", db_session_factory)
    monkeypatch.setattr(tg_store_module, "SessionLocal", db_session_factory)
    monkeypatch.setattr(tg_ticket_module, "SessionLocal", db_session_factory)

    # Fresh schema per test
    Base.metadata.drop_all(bind=db_engine)
    Base.metadata.create_all(bind=db_engine)

    yield


@pytest.fixture
def ticket_store():
    from app.core.store import DbTicketStore

    return DbTicketStore()


@pytest.fixture
def store_with_data(ticket_store):
    """DbTicketStore with 3 tickets for filtering/statistics tests."""
    ticket_store.add(
        {
            "full_name": "иванов иван",
            "facility": "Завод Казань",
            "phone": "+7 (999) 111-11-11",
            "email": "ivan@test.ru",
            "device_numbers": "нк-001",
            "device_type": "Тип А",
            "original_text": "Прибор не работает срочно!",
            "emotional_tone": "Негатив",
            "category": "Неисправность",
            "issue_summary": "Авария оборудования",
            "ai_response": "Ответ",
            "status": "Новое",
        }
    )
    ticket_store.add(
        {
            "full_name": "петрова светлана",
            "facility": "ооо газснаб",
            "phone": "+7 (347) 222-22-22",
            "email": "petra@test.ru",
            "device_numbers": "А-2241",
            "device_type": "Тип Б",
            "original_text": "Нужен паспорт на прибор.",
            "emotional_tone": "Нейтрально",
            "category": "Документация",
            "issue_summary": "Запрос документов",
            "ai_response": "Ответ",
            "status": "В работе",
        }
    )
    ticket_store.add(
        {
            "full_name": "смирнов алексей",
            "facility": "ао нефтехим",
            "phone": "+7 (855) 333-33-33",
            "email": "smir@test.ru",
            "device_numbers": "нк-002",
            "device_type": "Тип В",
            "original_text": "Спасибо за помощь с калибровкой!",
            "emotional_tone": "Позитив",
            "category": "Калибровка",
            "issue_summary": "Калибровка выполнена",
            "ai_response": "Ответ",
            "status": "Закрыто",
        }
    )
    return ticket_store


@pytest.fixture
def client(ticket_store, monkeypatch):
    """FastAPI TestClient with patched ticket_store."""
    import app.core.store as store_module
    import app.services.ticket_service as svc_module
    from app.main import create_app

    monkeypatch.setattr(store_module, "ticket_store", ticket_store)
    monkeypatch.setattr(svc_module, "ticket_store", ticket_store)

    application = create_app()
    with TestClient(application) as c:
        yield c


@pytest.fixture
def client_with_data(store_with_data, monkeypatch):
    """FastAPI TestClient with 3 prefilled tickets."""
    import app.core.store as store_module
    import app.services.ticket_service as svc_module
    from app.main import create_app

    monkeypatch.setattr(store_module, "ticket_store", store_with_data)
    monkeypatch.setattr(svc_module, "ticket_store", store_with_data)

    application = create_app()
    with TestClient(application) as c:
        yield c
