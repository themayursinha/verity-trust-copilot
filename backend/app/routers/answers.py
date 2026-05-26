from datetime import date
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_engine import EvidenceChunk, get_ai_engine
from app.core.engine import parse_date
from app.core.file_parser import parse_questionnaire_file
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.answer import Answer, AnswerGeneration, Approval
from app.models.audit_log import AuditLog
from app.models.evidence import EvidenceRecord
from app.models.questionnaire import Questionnaire
from app.models.user import User
from app.schemas.answer import (
    AnswerAssignmentRequest,
    AnswerBulkAssignmentRequest,
    AnswerGenerateRequest,
    AnswerGenerationResponse,
    AnswerResponse,
    LearnFromApprovalRequest,
    QuestionnaireCreate,
    QuestionnaireResponse,
)
from app.services.llm_service import generate_llm_answer

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
QUESTIONS_PATH = DATA_DIR / "questions.json"

router = APIRouter(prefix="/api/v1/answers", tags=["answers"])


def _orm_to_evidence_chunks(records: list[EvidenceRecord]) -> list[EvidenceChunk]:
    chunks: list[EvidenceChunk] = []
    for rec in records:
        for snippet_text in rec.snippets or []:
            chunks.append(
                EvidenceChunk(
                    evidence_id=rec.id,
                    title=rec.title,
                    evidence_type=rec.type,
                    frameworks=rec.frameworks or [],
                    control_ids=rec.control_ids or [],
                    last_reviewed=rec.last_reviewed,
                    owner=rec.owner,
                    snippet=snippet_text,
                    summary=rec.summary or "",
                )
            )
    return chunks


def _build_answer_response(a: Answer) -> AnswerResponse:
    return AnswerResponse(
        id=a.id,
        generation_id=a.generation_id,
        question=a.question,
        answer_text=a.answer_text,
        confidence=a.confidence,
        confidence_score=None,
        confidence_rationale=a.confidence_rationale,
        needs_human_review=a.needs_human_review,
        citations=a.citations or [],
        freshness=a.freshness or [],
        assignee_id=a.assignee_id,
        order_index=a.order_index or 0,
        source=a.source or "ai",
        created_at=a.created_at,
    )


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
                answers=[_build_answer_response(a) for a in answers],
                questionnaire_id=gen.questionnaire_id,
                original_filename=gen.original_filename,
                original_format=gen.original_format,
                engine_used=gen.engine_used or "ai",
                created_at=gen.created_at,
            )
        )
    return response


@router.get("/assigned", response_model=list[AnswerResponse])
async def list_assigned_answers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Answer)
        .join(AnswerGeneration, Answer.generation_id == AnswerGeneration.id)
        .where(
            Answer.assignee_id == current_user.id,
            AnswerGeneration.org_id == current_user.org_id,
        )
        .order_by(Answer.created_at.desc())
    )
    answers = result.scalars().all()
    return [_build_answer_response(a) for a in answers]


@router.get("/sample", response_model=dict)
async def get_sample_questions(
    current_user: User = Depends(get_current_active_user),
):
    from app.core.engine import load_questions

    questions = load_questions(QUESTIONS_PATH)
    return {"questions": questions}


@router.get("/knowledge-base/search", response_model=dict)
async def search_knowledge_base(
    q: str = Query(..., description="Search query for knowledge base"),
    current_user: User = Depends(get_current_active_user),
):
    engine = get_ai_engine()
    results = engine.search_knowledge_base(q, top_k=3)
    return {"query": q, "results": results, "count": len(results)}


@router.get("/questionnaires", response_model=list[QuestionnaireResponse])
async def list_questionnaires(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Questionnaire)
        .where(Questionnaire.org_id == current_user.org_id)
        .order_by(Questionnaire.created_at.desc())
    )
    questionnaires = result.scalars().all()
    return [
        QuestionnaireResponse(
            id=q.id,
            org_id=q.org_id,
            name=q.name,
            original_filename=q.original_filename,
            original_format=q.original_format,
            question_count=q.question_count,
            answered_count=q.answered_count,
            status=q.status,
            created_at=q.created_at,
            updated_at=q.updated_at,
        )
        for q in questionnaires
    ]


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

    ans_result = await db.execute(select(Answer).where(Answer.generation_id == gen.id).order_by(Answer.order_index))
    answers = ans_result.scalars().all()

    return AnswerGenerationResponse(
        id=gen.id,
        org_id=gen.org_id,
        as_of_date=gen.as_of_date.isoformat() if gen.as_of_date else None,
        confidence_counts=gen.confidence_counts or {},
        answers=[_build_answer_response(a) for a in answers],
        questionnaire_id=gen.questionnaire_id,
        original_filename=gen.original_filename,
        original_format=gen.original_format,
        engine_used=gen.engine_used or "ai",
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

    ev_result = await db.execute(
        select(EvidenceRecord).where(EvidenceRecord.org_id == current_user.org_id)
    )
    evidence_records = ev_result.scalars().all()

    chunks = _orm_to_evidence_chunks(evidence_records)

    engine = get_ai_engine()
    engine.index_evidence(chunks)
    use_ai = engine.is_available

    high_count = 0
    medium_count = 0
    low_count = 0

    answer_items: list[dict[str, Any]] = []
    for i, question in enumerate(body.questions):
        results = engine.search(question, top_k=5)

        confidence, confidence_score, rationale = engine.compute_confidence(results, use_ai=use_ai)
        citations = engine.build_citations(results)
        freshness = engine.build_freshness(results)

        if body.use_llm and settings.llm_configured and results:
            evidence_context = engine.build_evidence_context(results)
            llm_result = await generate_llm_answer(question, evidence_context)
            if "error" not in llm_result:
                answer_text = llm_result["answer_text"]
                source = "llm"
            else:
                answer_text = engine.generate_synthetic_answer(question, results)
                source = "ai"
        else:
            answer_text = engine.generate_synthetic_answer(question, results)
            source = "ai"

        if confidence == "high":
            high_count += 1
        elif confidence == "medium":
            medium_count += 1
        else:
            low_count += 1

        answer_items.append({
            "question": question,
            "answer_text": answer_text,
            "confidence": confidence,
            "confidence_score": confidence_score,
            "confidence_rationale": rationale,
            "needs_human_review": confidence != "high",
            "citations": citations,
            "freshness": freshness,
            "source": source,
            "order_index": i,
        })

    generation = AnswerGeneration(
        org_id=current_user.org_id,
        as_of_date=as_of,
        confidence_counts={"high": high_count, "medium": medium_count, "low": low_count},
        questionnaire_id=body.questionnaire_id,
        engine_used="ai" if use_ai else "bm25",
    )
    db.add(generation)
    await db.flush()

    answer_objs: list[Answer] = []
    for item in answer_items:
        answer_obj = Answer(
            generation_id=generation.id,
            question=item["question"],
            answer_text=item["answer_text"],
            confidence=item["confidence"],
            confidence_score=int(item["confidence_score"] * 100),
            confidence_rationale=item["confidence_rationale"],
            needs_human_review=item["needs_human_review"],
            citations=item["citations"],
            freshness=item["freshness"],
            source=item["source"],
            order_index=item["order_index"],
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
        changes={
            "count": len(answer_items),
            "engine": "ai" if use_ai else "bm25",
            "llm_used": body.use_llm and settings.llm_configured,
            "confidence": {"high": high_count, "medium": medium_count, "low": low_count},
        },
    )
    db.add(audit)

    if body.questionnaire_id:
        await db.execute(
            update(Questionnaire)
            .where(Questionnaire.id == body.questionnaire_id)
            .values(answered_count=len(answer_items), status="in_progress")
        )

    await db.commit()
    await db.refresh(generation)
    for a in answer_objs:
        await db.refresh(a)

    return AnswerGenerationResponse(
        id=generation.id,
        org_id=generation.org_id,
        as_of_date=generation.as_of_date.isoformat() if generation.as_of_date else None,
        confidence_counts=generation.confidence_counts or {},
        answers=[_build_answer_response(a) for a in answer_objs],
        questionnaire_id=generation.questionnaire_id,
        original_filename=generation.original_filename,
        original_format=generation.original_format,
        engine_used=generation.engine_used or "ai",
        created_at=generation.created_at,
    )


@router.post("/regenerate/{answer_id}", response_model=AnswerResponse)
async def regenerate_single_answer(
    answer_id: str,
    body: AnswerGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    ans_result = await db.execute(
        select(Answer).join(AnswerGeneration).where(
            Answer.id == answer_id,
            AnswerGeneration.org_id == current_user.org_id,
        )
    )
    answer = ans_result.scalar_one_or_none()
    if not answer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found")

    if not body.questions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide at least one question.")

    question = body.questions[0]

    ev_result = await db.execute(
        select(EvidenceRecord).where(EvidenceRecord.org_id == current_user.org_id)
    )
    evidence_records = ev_result.scalars().all()
    chunks = _orm_to_evidence_chunks(evidence_records)

    engine = get_ai_engine()
    engine.index_evidence(chunks)
    use_ai = engine.is_available

    results = engine.search(question, top_k=5)
    confidence, confidence_score, rationale = engine.compute_confidence(results, use_ai=use_ai)
    citations = engine.build_citations(results)
    freshness = engine.build_freshness(results)

    if body.use_llm and settings.llm_configured and results:
        evidence_context = engine.build_evidence_context(results)
        llm_result = await generate_llm_answer(question, evidence_context)
        if "error" not in llm_result:
            answer_text = llm_result["answer_text"]
            source = "llm"
        else:
            answer_text = engine.generate_synthetic_answer(question, results)
            source = "ai"
    else:
        answer_text = engine.generate_synthetic_answer(question, results)
        source = "ai"

    answer.question = question
    answer.answer_text = answer_text
    answer.confidence = confidence
    answer.confidence_score = int(confidence_score * 100)
    answer.confidence_rationale = rationale
    answer.needs_human_review = confidence != "high"
    answer.citations = citations
    answer.freshness = freshness
    answer.source = source

    await db.commit()
    await db.refresh(answer)
    return _build_answer_response(answer)


@router.post("/import-file")
async def import_questions_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    try:
        questions = await parse_questionnaire_file(file)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No questions found in the file. Please check the format.",
        )

    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else "txt"

    return {
        "questions": questions,
        "count": len(questions),
        "filename": file.filename,
        "format": ext,
    }


@router.post("/assign", response_model=AnswerResponse)
async def assign_answer(
    body: AnswerAssignmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    ans_result = await db.execute(
        select(Answer).join(AnswerGeneration).where(
            Answer.id == body.answer_id,
            AnswerGeneration.org_id == current_user.org_id,
        )
    )
    answer = ans_result.scalar_one_or_none()
    if not answer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found")

    assignee_result = await db.execute(
        select(User).where(User.id == body.assignee_id, User.org_id == current_user.org_id)
    )
    assignee = assignee_result.scalar_one_or_none()
    if not assignee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee not found in your organization")

    answer.assignee_id = body.assignee_id

    audit = AuditLog(
        org_id=current_user.org_id,
        user_id=current_user.id,
        resource_type="answer",
        resource_id=body.answer_id,
        action="assign",
        changes={"assignee_id": body.assignee_id},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(answer)
    return _build_answer_response(answer)


@router.post("/bulk-assign", response_model=dict)
async def bulk_assign_answers(
    body: AnswerBulkAssignmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    assignee_result = await db.execute(
        select(User).where(User.id == body.assignee_id, User.org_id == current_user.org_id)
    )
    if not assignee_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee not found in your organization")

    assigned = 0
    for answer_id in body.answer_ids:
        ans_result = await db.execute(
            select(Answer).join(AnswerGeneration).where(
                Answer.id == answer_id,
                AnswerGeneration.org_id == current_user.org_id,
            )
        )
        answer = ans_result.scalar_one_or_none()
        if answer:
            answer.assignee_id = body.assignee_id
            assigned += 1

    await db.commit()
    return {"assigned_count": assigned, "assignee_id": body.assignee_id}


@router.put("/{answer_id}", response_model=AnswerResponse)
async def update_answer(
    answer_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    ans_result = await db.execute(
        select(Answer).join(AnswerGeneration).where(
            Answer.id == answer_id,
            AnswerGeneration.org_id == current_user.org_id,
        )
    )
    answer = ans_result.scalar_one_or_none()
    if not answer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found")

    allowed_fields = {"answer_text", "confidence", "needs_human_review"}
    for key, value in body.items():
        if key in allowed_fields:
            setattr(answer, key, value)

    await db.commit()
    await db.refresh(answer)
    return _build_answer_response(answer)


@router.post("/learn", response_model=dict)
async def learn_from_approvals(
    body: LearnFromApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    learned = 0
    entries: list[dict[str, Any]] = []

    for answer_id in body.answer_ids:
        ans_result = await db.execute(
            select(Answer).join(AnswerGeneration).where(
                Answer.id == answer_id,
                AnswerGeneration.org_id == current_user.org_id,
            )
        )
        answer = ans_result.scalar_one_or_none()
        if not answer:
            continue

        approval_result = await db.execute(
            select(Approval).where(
                Approval.answer_id == answer_id,
                Approval.status == "approved",
            )
        )
        approval = approval_result.scalar_one_or_none()

        if approval and answer.question and answer.answer_text:
            entries.append({
                "question": answer.question,
                "answer_text": answer.answer_text,
                "confidence": answer.confidence,
                "citations": answer.citations,
                "learned_at": date.today().isoformat(),
            })
            learned += 1

    if entries:
        engine = get_ai_engine()
        engine.index_knowledge_base(entries)

    return {"learned": learned, "total_kb_entries": len(entries)}


@router.post("/questionnaires", response_model=QuestionnaireResponse, status_code=status.HTTP_201_CREATED)
async def create_questionnaire(
    body: QuestionnaireCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    questionnaire = Questionnaire(
        org_id=current_user.org_id,
        name=body.name,
        original_filename=body.original_filename,
        original_format=body.original_format,
        original_content=body.original_content,
        question_count=len(body.questions) if body.questions else 0,
        status="draft",
        created_by=current_user.id,
    )
    db.add(questionnaire)
    await db.commit()
    await db.refresh(questionnaire)
    return QuestionnaireResponse(
        id=questionnaire.id,
        org_id=questionnaire.org_id,
        name=questionnaire.name,
        original_filename=questionnaire.original_filename,
        original_format=questionnaire.original_format,
        question_count=questionnaire.question_count,
        answered_count=questionnaire.answered_count,
        status=questionnaire.status,
        created_at=questionnaire.created_at,
        updated_at=questionnaire.updated_at,
    )


@router.put("/questionnaires/{questionnaire_id}", response_model=QuestionnaireResponse)
async def update_questionnaire_status(
    questionnaire_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Questionnaire).where(
            Questionnaire.id == questionnaire_id,
            Questionnaire.org_id == current_user.org_id,
        )
    )
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questionnaire not found")

    if "status" in body:
        q.status = body["status"]
    if "name" in body:
        q.name = body["name"]

    await db.commit()
    await db.refresh(q)
    return QuestionnaireResponse(
        id=q.id,
        org_id=q.org_id,
        name=q.name,
        original_filename=q.original_filename,
        original_format=q.original_format,
        question_count=q.question_count,
        answered_count=q.answered_count,
        status=q.status,
        created_at=q.created_at,
        updated_at=q.updated_at,
    )
