from __future__ import annotations

from datetime import datetime, timedelta, timezone


def test_create_link_token_persists_and_has_ttl(db_session_factory):
    from app.core.telegram_store import DbTelegramChannelStore
    from app.core.models import TelegramLinkToken

    store = DbTelegramChannelStore()
    tok = store.create_link_token(ttl_minutes=10)
    assert tok.token

    exp = datetime.fromisoformat(tok.expires_at)
    assert exp.tzinfo is not None

    with db_session_factory() as db:
        row = db.get(TelegramLinkToken, tok.token)
        assert row is not None


def test_consume_token_registers_channel_and_is_one_time(db_session_factory):
    from app.core.telegram_store import DbTelegramChannelStore
    from app.core.models import TelegramLinkToken, TelegramChannel

    store = DbTelegramChannelStore()
    tok = store.create_link_token(ttl_minutes=10)

    ok = store.consume_token_and_register_channel(
        token=tok.token,
        chat_id=123,
        title="My Channel",
        chat_type="channel",
    )
    assert ok is True

    ok2 = store.consume_token_and_register_channel(
        token=tok.token,
        chat_id=123,
        title="My Channel",
        chat_type="channel",
    )
    assert ok2 is False

    channels = store.list_active_channels()
    assert channels and channels[0]["chat_id"] == 123
    assert channels[0]["active"] is True

    with db_session_factory() as db:
        token_row = db.get(TelegramLinkToken, tok.token)
        assert token_row.consumed_at is not None
        chan = db.get(TelegramChannel, 123)
        assert chan is not None


def test_expired_token_cannot_be_consumed(db_session_factory):
    from app.core.telegram_store import DbTelegramChannelStore
    from app.core.models import TelegramLinkToken

    store = DbTelegramChannelStore()
    tok = store.create_link_token(ttl_minutes=10)

    # Force expiry in DB
    with db_session_factory() as db:
        row = db.get(TelegramLinkToken, tok.token)
        row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.add(row)
        db.commit()

    assert store.consume_token_and_register_channel(tok.token, 1, "", "") is False
    assert store.list_active_channels() == []
