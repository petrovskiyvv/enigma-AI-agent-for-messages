from pydantic import BaseModel
from typing import Optional


class TicketCreate(BaseModel):
    full_name: str = ""
    facility: str = ""
    phone: str = ""
    email: str = ""
    device_numbers: str = ""
    device_type: str = ""
    original_text: str = ""


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    ai_response: Optional[str] = None
    full_name: Optional[str] = None
    facility: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    device_numbers: Optional[str] = None
    device_type: Optional[str] = None
    issue_summary: Optional[str] = None


class AnalyzeRequest(BaseModel):
    text: str


class StatsResponse(BaseModel):
    total: int
    by_tone: dict[str, int]
    by_category: dict[str, int]
    by_status: dict[str, int]
