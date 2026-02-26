from fastapi import APIRouter

from app.schemas.ticket import AnalyzeRequest
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/analyze", tags=["analyze"])
service = TicketService()


@router.post("")
async def analyze_email(request: AnalyzeRequest):
    return service.analyze_and_create(request.text)
