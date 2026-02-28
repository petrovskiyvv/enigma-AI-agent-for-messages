import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def telegram_client(tmp_path, monkeypatch):
    from app.main import create_app

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
