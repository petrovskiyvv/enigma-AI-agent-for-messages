from fastapi import APIRouter, HTTPException

from app.core.telegram_store import JsonTelegramChannelStore

router = APIRouter(prefix="/telegram", tags=["telegram"])
store = JsonTelegramChannelStore()


@router.post("/link-token")
def create_link_token():
    tok = store.create_link_token()
    return {"token": tok.token, "expires_at": tok.expires_at}


@router.get("/channels")
def list_channels():
    return {"channels": store.list_active_channels()}
