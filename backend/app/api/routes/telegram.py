from fastapi import APIRouter

from app.core.telegram_store import telegram_store
from app.core.config import settings

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/link-token")
def create_link_token():
    tok = telegram_store.create_link_token(ttl_minutes=settings.telegram_link_token_ttl_minutes)
    return {"token": tok.token, "expires_at": tok.expires_at}


@router.get("/channels")
def list_channels():
    return {"channels": telegram_store.list_active_channels()}
