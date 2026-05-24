from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.answer import Answer, AnswerGeneration, Approval
from app.models.user import User

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])


@router.get("/", response_model=list[dict])
async def list_approvals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Approval, Answer.question, Answer.id)
        .join(Answer, Approval.answer_id == Answer.id)
        .join(AnswerGeneration, Answer.generation_id == AnswerGeneration.id)
        .where(AnswerGeneration.org_id == current_user.org_id)
        .order_by(Approval.created_at.desc())
    )
    rows = result.all()
    return [
        {
            "id": app.id,
            "answer_id": app.answer_id,
            "question": question,
            "user_id": app.user_id,
            "status": app.status,
            "notes": app.notes,
            "created_at": app.created_at.isoformat(),
        }
        for app, question, answer_id in rows
    ]


@router.post("/", response_model=dict)
async def set_approval(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    question = body.get("question")
    if not isinstance(question, str) or not question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Send a non-empty 'question' string.",
        )

    approval_status = body.get("status", "unreviewed")
    if approval_status not in ("unreviewed", "approved", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'approved', 'rejected', or 'unreviewed'.",
        )

    notes = str(body.get("notes", "")).strip()

    ans_result = await db.execute(
        select(Answer)
        .join(AnswerGeneration, Answer.generation_id == AnswerGeneration.id)
        .where(
            Answer.question == question.strip(),
            AnswerGeneration.org_id == current_user.org_id,
        )
    )
    answer = ans_result.scalar_one_or_none()
    if not answer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found for this question.")

    existing_result = await db.execute(
        select(Approval).where(
            Approval.answer_id == answer.id,
            Approval.user_id == current_user.id,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.status = approval_status
        existing.notes = notes
        db.add(existing)
        await db.commit()
        await db.refresh(existing)
        return {
            "id": existing.id,
            "answer_id": existing.answer_id,
            "user_id": existing.user_id,
            "status": existing.status,
            "notes": existing.notes,
            "question": answer.question,
            "created_at": existing.created_at.isoformat(),
        }

    approval = Approval(
        answer_id=answer.id,
        user_id=current_user.id,
        status=approval_status,
        notes=notes,
    )
    db.add(approval)
    await db.commit()
    await db.refresh(approval)

    return {
        "id": approval.id,
        "answer_id": approval.answer_id,
        "user_id": approval.user_id,
        "status": approval.status,
        "notes": approval.notes,
        "question": answer.question,
        "created_at": approval.created_at.isoformat(),
    }
