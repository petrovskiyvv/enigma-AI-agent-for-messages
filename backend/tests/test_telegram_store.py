import json
from datetime import datetime, timedelta, timezone

import pytest


@pytest.fixture
def tmp_telegram_store(tmp_path, monkeypatch):
    """Isolated JsonTelegramChannelStore backed by a temp file."""
    from app.core import telegram_store as store_module
    from app.core.config import settings

    path = tmp_path / "telegram_channels_test.json"
    monkeypatch.setattr(settings, "telegram_store_path", str(path))

    base_now = datetime(2030, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(store_module, "_utc_now", lambda: base_now)

    return store_module.JsonTelegramChannelStore(path=str(path))


def test_create_link_token_persists_and_has_ttl(tmp_telegram_store, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "telegram_link_token_ttl_minutes", 10)
    tok = tmp_telegram_store.create_link_token()

    assert tok.token
    exp = datetime.fromisoformat(tok.expires_at)
    assert exp.tzinfo is not None

    data = json.loads(tmp_telegram_store._path.read_text(encoding="utf-8"))
    assert any(t["token"] == tok.token for t in data["pending_tokens"])


def test_consume_token_registers_channel_and_is_one_time(tmp_telegram_store):
    tok = tmp_telegram_store.create_link_token()

    ok = tmp_telegram_store.consume_token_and_register_channel(
        token=tok.token,
        chat_id=123,
        title="My Channel",
        chat_type="channel",
    )
    assert ok is True

    ok2 = tmp_telegram_store.consume_token_and_register_channel(
        token=tok.token,
        chat_id=123,
        title="My Channel",
        chat_type="channel",
    )
    assert ok2 is False

    channels = tmp_telegram_store.list_active_channels()
    assert channels and channels[0]["chat_id"] == 123
    assert channels[0]["active"] is True


def test_expired_tokens_are_purged(tmp_path, monkeypatch):
    from app.core import telegram_store as store_module
    from app.core.config import settings

    path = tmp_path / "telegram_channels_test.json"
    monkeypatch.setattr(settings, "telegram_store_path", str(path))

    t0 = datetime(2030, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(store_module, "_utc_now", lambda: t0)

    store = store_module.JsonTelegramChannelStore(path=str(path))
    tok = store.create_link_token()

    t1 = t0 + timedelta(hours=1)
    monkeypatch.setattr(store_module, "_utc_now", lambda: t1)

    assert store.consume_token_and_register_channel(tok.token, 1, "", "") is False

    # purge happens in-memory; persist is triggered on the next successful operation
    assert store._data["pending_tokens"] == []

    # force persist via another token creation
    _ = store.create_link_token()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert all(t["token"] != tok.token for t in data["pending_tokens"])
