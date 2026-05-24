"""Report generation router — SOC 2 Type II and other compliance reports."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.answer import Answer, AnswerGeneration
from app.models.audit_log import AuditLog
from app.models.evidence import EvidenceRecord
from app.models.pentest import Pentest
from app.models.policy import Policy
from app.models.user import User

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/soc2")
async def generate_soc2_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    org_id = current_user.org_id
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    evidence_result = await db.execute(
        select(EvidenceRecord).where(EvidenceRecord.org_id == org_id)
    )
    evidence = evidence_result.scalars().all()

    policies_result = await db.execute(
        select(Policy).where(Policy.org_id == org_id)
    )
    policies = policies_result.scalars().all()

    pentests_result = await db.execute(
        select(Pentest).where(Pentest.org_id == org_id)
    )
    pentests = pentests_result.scalars().all()

    gen_result = await db.execute(
        select(AnswerGeneration).where(AnswerGeneration.org_id == org_id)
    )
    generations = gen_result.scalars().all()

    all_answers = []
    for gen in generations:
        ans_result = await db.execute(
            select(Answer).where(Answer.generation_id == gen.id)
        )
        all_answers.extend(ans_result.scalars().all())

    frameworks = {"iso-27001": [], "soc-2": [], "gdpr": [], "dora": []}
    for ev in evidence:
        for fw in (ev.frameworks or []):
            fw_key = fw.lower().replace(" ", "-").replace("_", "-")
            if fw_key in frameworks:
                frameworks[fw_key].append(ev.title)

    lines = [
        "# SOC 2 Type II Compliance Report",
        "",
        f"**Generated:** {now}",
        f"**Organization ID:** {org_id}",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        f"This report provides an overview of the organization's compliance posture as of {now}.",
        "",
        f"- **Evidence Records:** {len(evidence)}",
        f"- **Active Policies:** {sum(1 for p in policies if p.status == 'active')}",
        f"- **Completed Pentests:** {sum(1 for p in pentests if p.status == 'completed')}",
        f"- **Security Answers Generated:** {len(all_answers)}",
        "",
        "---",
        "",
        "## 2. Framework Coverage",
        "",
        "| Framework | Evidence Count | Controls |",
        "|-----------|---------------|----------|",
    ]

    for fw_name, titles in frameworks.items():
        display = fw_name.replace("-", " ").title()
        lines.append(f"| {display} | {len(titles)} | {', '.join(titles) if titles else 'None'} |")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Evidence Library",
        "",
    ])

    for ev in evidence:
        days_ago = (datetime.now(timezone.utc).date() - ev.last_reviewed).days if ev.last_reviewed else 999
        status = "Fresh" if days_ago <= 180 else ("Stale" if days_ago <= 365 else "Outdated")
        lines.append(f"### {ev.title}")
        lines.append(f"- **Type:** {ev.type}")
        lines.append(f"- **Owner:** {ev.owner}")
        lines.append(f"- **Last Reviewed:** {ev.last_reviewed} ({days_ago} days ago — {status})")
        lines.append(f"- **Frameworks:** {', '.join(ev.frameworks or []) or 'None'}")
        lines.append(f"- **Controls:** {', '.join(ev.control_ids or []) or 'None'}")
        lines.append(f"- **Summary:** {ev.summary}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 4. Policies",
        "",
    ])

    for p in policies:
        lines.append(f"### {p.title}")
        lines.append(f"- **Status:** {p.status}")
        lines.append(f"- **Version:** {p.version}")
        lines.append(f"- **Category:** {p.category}")
        if p.next_review:
            lines.append(f"- **Next Review:** {p.next_review}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 5. Penetration Tests",
        "",
    ])

    for pt in pentests:
        lines.append(f"### {pt.title}")
        lines.append(f"- **Status:** {pt.status}")
        lines.append(f"- **Scope:** {pt.scope}")
        lines.append(f"- **Methodology:** {pt.methodology}")
        if pt.start_date:
            lines.append(f"- **Start Date:** {pt.start_date}")
        if pt.end_date:
            lines.append(f"- **End Date:** {pt.end_date}")
        findings = pt.findings or []
        if findings:
            lines.append(f"- **Findings:** {len(findings)}")
            for f in findings[:10]:
                lines.append(f"  - [{f.get('severity', 'N/A').upper()}] {f.get('title', 'Untitled')} — {f.get('status', 'unknown')}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 6. Security Answers",
        "",
    ])

    approved = [a for a in all_answers if a.needs_human_review is False]
    needs_review = [a for a in all_answers if a.needs_human_review is True]

    lines.append(f"- **Approved Answers:** {len(approved)}")
    lines.append(f"- **Needs Review:** {len(needs_review)}")
    lines.append("")

    if all_answers:
        lines.append("### Generated Answers")
        lines.append("")
        for a in all_answers[:20]:
            conf = a.confidence or "unknown"
            lines.append(f"#### Q: {a.question}")
            lines.append(f"**Confidence:** {conf.upper()} | **Needs Review:** {a.needs_human_review}")
            lines.append(f"{a.answer_text[:500]}{'...' if len(a.answer_text or '') > 500 else ''}")
            lines.append("")

    lines.extend([
        "---",
        "",
        "*This report was automatically generated by Verity Trust Copilot.*",
        "*Review all content before sharing with auditors or customers.*",
    ])

    markdown = "\n".join(lines)

    audit = AuditLog(
        org_id=org_id,
        user_id=current_user.id,
        resource_type="report",
        resource_id="soc2",
        action="export",
        changes={"evidence_count": len(evidence), "answers_count": len(all_answers)},
    )
    db.add(audit)
    await db.commit()

    return {
        "format": "markdown",
        "report": markdown,
        "generated_at": now,
        "stats": {
            "evidence": len(evidence),
            "policies": len(policies),
            "pentests": len(pentests),
            "answers": len(all_answers),
            "approved_answers": len(approved),
            "needs_review": len(needs_review),
        },
    }
