"""Financial learning endpoints."""
from fastapi import APIRouter
from services.learning_service import list_lessons

router = APIRouter(prefix="/api/learning", tags=["Learning"])


@router.get("/lessons")
async def lessons():
    return list_lessons()
