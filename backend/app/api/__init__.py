from fastapi import APIRouter

from app.api.routes import tickets, analyze, utility, telegram, knowledge

api_router = APIRouter(prefix="/api")
api_router.include_router(tickets.router)
api_router.include_router(analyze.router)
api_router.include_router(utility.router)
api_router.include_router(telegram.router)
api_router.include_router(knowledge.router)
