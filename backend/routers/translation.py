"""On-demand translation endpoints."""
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.translation_service import translate_texts
from utils.api_response import error_response

router = APIRouter(prefix="/api/translation", tags=["Translation"])


class TranslationRequest(BaseModel):
    texts: List[str] = Field(default_factory=list, max_length=8)
    target_language: str = "zh-CN"


@router.post("/texts")
async def translate(request: TranslationRequest):
    try:
        return translate_texts(request.texts, request.target_language)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=error_response("TRANSLATION_FAILED", "翻译服务暂时不可用，请稍后重试。"),
        ) from exc
