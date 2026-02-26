from fastapi import APIRouter, HTTPException
from typing import Optional

from app.schemas.ticket import TicketCreate, TicketUpdate
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["tickets"])
service = TicketService()


@router.get("")
async def list_tickets(
    status: Optional[str] = None,
    tone: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
):
    return service.get_list(status=status, tone=tone, category=category, search=search)


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: int):
    ticket = service.get_one(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    return ticket


@router.post("", status_code=201)
async def create_ticket(data: TicketCreate):
    return service.create(data)


@router.patch("/{ticket_id}")
async def update_ticket(ticket_id: int, data: TicketUpdate):
    ticket = service.update(ticket_id, data)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    return ticket
