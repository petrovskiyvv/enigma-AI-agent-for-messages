import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def telegram_client(tmp_path, monkeypatch):
    from app.core.telegram_store import JsonTelegramChannelStore
    from app.main import create_app
    import app.api.routes.telegram as telegram_route
    from app.core.config import settings

    monkeypatch.setattr(settings, "telegram_store_path", str(tmp_path / "channels.json"))
    telegram_route.store = JsonTelegramChannelStore(path=str(tmp_path / "channels.json"))

    app = create_app()
    with TestClient(app) as c:
        yield c


def test_create_link_token_and_channels_flow(telegram_client):
    r = telegram_client.post("/api/telegram/link-token")
    assert r.status_code == 200
    payload = r.json()
    assert "token" in payload and "expires_at" in payload

    r2 = telegram_client.get("/api/telegram/channels")
    assert r2.status_code == 200
    assert r2.json() == {"channels": []}
