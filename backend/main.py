from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import datetime

app = FastAPI(title="Enigma Support API")

# Настройка CORS для запросов от Flutter Web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic модель для валидации данных
class Ticket(BaseModel):
    full_name: str
    facility: str
    email: str
    issue_summary: str
    emotional_tone: str = "Нейтраль"

@app.get("/api/tickets")
async def get_tickets():
    """Эндпоинт для получения списка писем. (Пока возвращает мок-данные для фронтенда)"""
    return [
        {
            "id": 1,
            "date": datetime.datetime.now().isoformat(),
            "full_name": "Иванов И.И.",
            "facility": "Объект А",
            "email": "ivanov@test.com",
            "issue_summary": "Ошибка сенсора",
            "emotional_tone": "Негатив"
        }
    ]

@app.post("/api/tickets")
async def create_ticket(ticket: Ticket):
    """Эндпоинт для добавления письма """
    return {"status": "success", "message": "Ticket added", "data": ticket}