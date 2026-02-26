import csv
import io

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.ticket_service import TicketService

router = APIRouter(tags=["utility"])
service = TicketService()

_CSV_FIELDS = [
    "id", "created_at", "full_name", "facility", "phone", "email",
    "device_numbers", "device_type", "emotional_tone", "category",
    "issue_summary", "status",
]


@router.get("/stats")
async def get_stats():
    return service.get_stats()


@router.get("/export/csv")
async def export_csv():
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=_CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(service.get_list())
    output.seek(0)

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tickets_export.csv"},
    )
