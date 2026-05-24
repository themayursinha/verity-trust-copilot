import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.engine import export_csv
from app.dependencies import get_current_active_user
from app.models.user import User

ROOT = Path(__file__).resolve().parent.parent.parent.parent
OUTPUT_DIR = ROOT / "outputs"

router = APIRouter(prefix="/api/v1/export", tags=["export"])


class ExportAnswerRequest(BaseModel):
    answer: dict[str, Any]


def render_customer_ready_markdown(answer: dict[str, Any]) -> str:
    lines = [
        "# Customer Security Answer",
        "",
        "## Question",
        "",
        str(answer.get("question", "")),
        "",
        "## Draft Answer",
        "",
        str(answer.get("answer", "")),
        "",
        f"**Confidence:** {answer.get('confidence', 'unknown')}",
        f"**Needs human review:** {str(answer.get('needs_human_review', False)).lower()}",
        "",
        "## Sources",
        "",
    ]
    citations = answer.get("citations") if isinstance(answer.get("citations"), list) else []
    if citations:
        for citation in citations:
            if not isinstance(citation, dict):
                continue
            lines.append(
                "- {citation} {title} ({source_id}, reviewed {last_reviewed})".format(
                    citation=citation.get("citation", ""),
                    title=citation.get("title", ""),
                    source_id=citation.get("source_id", ""),
                    last_reviewed=citation.get("last_reviewed", ""),
                )
            )
    else:
        lines.append("- No sources found. Do not send without review.")
    lines.extend(["", "## Freshness", ""])
    freshness = answer.get("freshness") if isinstance(answer.get("freshness"), list) else []
    if freshness:
        for item in freshness:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- {source}: {status}, reviewed {last_reviewed}, {age_days} days old".format(
                    source=item.get("source", ""),
                    status=item.get("status", ""),
                    last_reviewed=item.get("last_reviewed", ""),
                    age_days=item.get("age_days", ""),
                )
            )
    else:
        lines.append("- No freshness checks available.")
    lines.append("")
    return "\n".join(lines)


@router.post("/", response_model=dict)
async def export_markdown(
    body: ExportAnswerRequest,
    current_user: User = Depends(get_current_active_user),
):
    answer = body.answer
    if not isinstance(answer, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Send an answer object to export.")
    markdown = render_customer_ready_markdown(answer)
    return {"path": str(OUTPUT_DIR / "customer_ready_answer.md"), "markdown": markdown}


@router.post("/csv", response_model=dict)
async def export_csv_answer(
    body: ExportAnswerRequest,
    current_user: User = Depends(get_current_active_user),
):
    answer = body.answer
    if not isinstance(answer, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Send an answer object to export.")
    results = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "as_of_date": date.today().isoformat(),
        "summary": {
            "questions_processed": 1,
            "confidence_counts": {answer.get("confidence", "low"): 1},
            "human_reviews_required": 1 if answer.get("needs_human_review") else 0,
        },
        "answers": [answer],
    }
    csv_content = export_csv(results)
    return {"path": str(OUTPUT_DIR / "customer_ready_answer.csv"), "csv": csv_content}


@router.post("/json", response_model=dict)
async def export_json_answer(
    body: ExportAnswerRequest,
    current_user: User = Depends(get_current_active_user),
):
    answer = body.answer
    if not isinstance(answer, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Send an answer object to export.")
    results = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "as_of_date": date.today().isoformat(),
        "summary": {
            "questions_processed": 1,
            "confidence_counts": {answer.get("confidence", "low"): 1},
            "human_reviews_required": 1 if answer.get("needs_human_review") else 0,
        },
        "answers": [answer],
    }
    return {"path": str(OUTPUT_DIR / "customer_ready_answer.json"), "json": results}
