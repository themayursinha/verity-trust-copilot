"""LLM-powered answer suggestion router."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.evidence import EvidenceRecord
from app.models.user import User
from app.services.llm_providers import list_providers as get_providers, get_provider_config
from app.services.llm_service import generate_llm_answer


class LLMGenerateRequest(BaseModel):
    question: str


class LLMGenerateResponse(BaseModel):
    question: str
    answer_text: str
    model: str
    usage: dict
    evidence_used: int
    needs_human_review: bool = True
    source: str = "llm"


router = APIRouter(prefix="/api/v1/llm", tags=["llm"])


@router.get("/providers")
async def list_providers(
    current_user: User = Depends(get_current_active_user),
):
    providers = get_providers()
    return {
        "providers": providers,
        "current": settings.LLM_PROVIDER,
        "count": len(providers),
    }


@router.post("/suggest", response_model=LLMGenerateResponse)
async def suggest_answer(
    body: LLMGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not settings.llm_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM is not configured. Set LLM_API_KEY and LLM_PROVIDER in environment.",
        )

    result = await db.execute(
        select(EvidenceRecord).where(
            EvidenceRecord.org_id == current_user.org_id,
        )
    )
    evidence_records = result.scalars().all()

    if not evidence_records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No evidence records found. Upload evidence first before using LLM suggestions.",
        )

    evidence_context = [
        {
            "title": rec.title,
            "type": rec.type,
            "frameworks": rec.frameworks or [],
            "summary": rec.summary,
            "snippets": rec.snippets or [],
        }
        for rec in evidence_records
    ]

    llm_result = await generate_llm_answer(body.question, evidence_context)

    if "error" in llm_result:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=llm_result["error"],
        )

    return LLMGenerateResponse(
        question=body.question,
        answer_text=llm_result["answer_text"],
        model=llm_result["model"],
        usage=llm_result["usage"],
        evidence_used=len(evidence_records),
        needs_human_review=True,
        source="llm",
    )


@router.get("/status")
async def llm_status(
    current_user: User = Depends(get_current_active_user),
):
    provider_info = get_provider_config(settings.LLM_PROVIDER)
    provider_name = provider_info["name"] if provider_info else settings.LLM_PROVIDER

    return {
        "configured": settings.llm_configured,
        "provider": settings.LLM_PROVIDER,
        "provider_name": provider_name,
        "model": settings.LLM_MODEL,
        "api_type": provider_info.get("api_type", "openai") if provider_info else "openai",
        "synthesis_enabled": settings.AI_SYNTHESIS_ENABLED,
    }
