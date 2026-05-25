from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.engine import EvidenceSnippet, build_results, load_questions, parse_date
from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.answer import Answer, AnswerGeneration
from app.models.audit_log import AuditLog
from app.models.evidence import EvidenceRecord
from app.models.user import User
from app.schemas.answer import (
    AnswerGenerateRequest,
    AnswerGenerationResponse,
    AnswerResponse,
)

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
QUESTIONS_PATH = DATA_DIR / "questions.json"

router = APIRouter(prefix="/api/v1/answers", tags=["answers"])


def _orm_to_evidence_snippets(records: list[EvidenceRecord]) -> list[EvidenceSnippet]:
    snippets: list[EvidenceSnippet] = []
    for rec in records:
        for snippet_text in rec.snippets or []:
            snippets.append(
                EvidenceSnippet(
                    evidence_id=rec.id,
                    title=rec.title,
                    evidence_type=rec.type,
                    frameworks=rec.frameworks or [],
                    control_ids=rec.control_ids or [],
                    last_reviewed=rec.last_reviewed,
                    owner=rec.owner,
                    snippet=snippet_text,
                    summary=rec.summary,
                )
            )
    return snippets


@router.get("/", response_model=list[AnswerGenerationResponse])
async def list_answer_generations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    gen_result = await db.execute(
        select(AnswerGeneration)
        .where(AnswerGeneration.org_id == current_user.org_id)
        .order_by(AnswerGeneration.created_at.desc())
    )
    generations = gen_result.scalars().all()

    response: list[AnswerGenerationResponse] = []
    for gen in generations:
        ans_result = await db.execute(select(Answer).where(Answer.generation_id == gen.id))
        answers = ans_result.scalars().all()
        response.append(
            AnswerGenerationResponse(
                id=gen.id,
                org_id=gen.org_id,
                as_of_date=gen.as_of_date.isoformat() if gen.as_of_date else None,
                confidence_counts=gen.confidence_counts or {},
                answers=[
                    AnswerResponse(
                        id=a.id,
                        generation_id=a.generation_id,
                        question=a.question,
                        answer_text=a.answer_text,
                        confidence=a.confidence,
                        confidence_rationale=a.confidence_rationale,
                        needs_human_review=a.needs_human_review,
                        citations=a.citations or [],
                        freshness=a.freshness or [],
                        created_at=a.created_at,
                    )
                    for a in answers
                ],
                created_at=gen.created_at,
            )
        )
    return response


@router.get("/sample", response_model=dict)
async def get_sample_questions(
    current_user: User = Depends(get_current_active_user),
):
    questions = load_questions(QUESTIONS_PATH)
    return {"questions": questions}


@router.get("/{generation_id}", response_model=AnswerGenerationResponse)
async def get_answer_generation(
    generation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    gen_result = await db.execute(
        select(AnswerGeneration).where(
            AnswerGeneration.id == generation_id,
            AnswerGeneration.org_id == current_user.org_id,
        )
    )
    gen = gen_result.scalar_one_or_none()
    if not gen:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer generation not found")

    ans_result = await db.execute(select(Answer).where(Answer.generation_id == gen.id))
    answers = ans_result.scalars().all()

    return AnswerGenerationResponse(
        id=gen.id,
        org_id=gen.org_id,
        as_of_date=gen.as_of_date.isoformat() if gen.as_of_date else None,
        confidence_counts=gen.confidence_counts or {},
        answers=[
            AnswerResponse(
                id=a.id,
                generation_id=a.generation_id,
                question=a.question,
                answer_text=a.answer_text,
                confidence=a.confidence,
                confidence_rationale=a.confidence_rationale,
                needs_human_review=a.needs_human_review,
                citations=a.citations or [],
                freshness=a.freshness or [],
                created_at=a.created_at,
            )
            for a in answers
        ],
        created_at=gen.created_at,
    )


@router.post("/", response_model=AnswerGenerationResponse, status_code=status.HTTP_201_CREATED)
async def generate_answers(
    body: AnswerGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not body.questions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Add at least one security question.")

    as_of = parse_date(body.as_of) if body.as_of else date.today()

    ev_result = await db.execute(select(EvidenceRecord).where(EvidenceRecord.org_id == current_user.org_id))
    evidence_records = ev_result.scalars().all()
    evidence_list = _orm_to_evidence_snippets(evidence_records)

    result = build_results(body.questions, evidence_list, as_of)

    generation = AnswerGeneration(
        org_id=current_user.org_id,
        as_of_date=as_of,
        confidence_counts=result["summary"]["confidence_counts"],
    )
    db.add(generation)
    await db.flush()

    answer_objs: list[Answer] = []
    for item in result["answers"]:
        answer_obj = Answer(
            generation_id=generation.id,
            question=item["question"],
            answer_text=item["answer"],
            confidence=item["confidence"],
            confidence_rationale=item.get("confidence_rationale", ""),
            needs_human_review=item.get("needs_human_review", False),
            citations=item.get("citations", []),
            freshness=item.get("freshness", []),
        )
        db.add(answer_obj)
        answer_objs.append(answer_obj)
    await db.flush()

    audit = AuditLog(
        org_id=current_user.org_id,
        user_id=current_user.id,
        resource_type="answers",
        resource_id=generation.id,
        action="generate",
        changes={"count": len(result["answers"])},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(generation)
    for a in answer_objs:
        await db.refresh(a)

    return AnswerGenerationResponse(
        id=generation.id,
        org_id=generation.org_id,
        as_of_date=generation.as_of_date.isoformat() if generation.as_of_date else None,
        confidence_counts=generation.confidence_counts or {},
        answers=[
            AnswerResponse(
                id=a.id,
                generation_id=a.generation_id,
                question=a.question,
                answer_text=a.answer_text,
                confidence=a.confidence,
                confidence_rationale=a.confidence_rationale,
                needs_human_review=a.needs_human_review,
                citations=a.citations or [],
                freshness=a.freshness or [],
                created_at=a.created_at,
            )
            for a in answer_objs
        ],
        created_at=generation.created_at,
    )
