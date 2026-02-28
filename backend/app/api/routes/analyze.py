from fastapi import APIRouter

from app.schemas.ticket import AnalyzeRequest
from app.services.ticket_service import TicketService
from app.services.telegram_notifier import notify_new_ticket

router = APIRouter(prefix="/analyze", tags=["analyze"])
service = TicketService()


@router.post("")
async def analyze_email(request: AnalyzeRequest):
    ticket = service.analyze_and_create(request.text)
    await notify_new_ticket(ticket)
    return ticket
