"""Report generation router — SOC 2 Type II and other compliance reports."""

import io
import json
import zipfile
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
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

    evidence_result = await db.execute(select(EvidenceRecord).where(EvidenceRecord.org_id == org_id))
    evidence = evidence_result.scalars().all()

    policies_result = await db.execute(select(Policy).where(Policy.org_id == org_id))
    policies = policies_result.scalars().all()

    pentests_result = await db.execute(select(Pentest).where(Pentest.org_id == org_id))
    pentests = pentests_result.scalars().all()

    gen_result = await db.execute(select(AnswerGeneration).where(AnswerGeneration.org_id == org_id))
    generations = gen_result.scalars().all()

    all_answers = []
    for gen in generations:
        ans_result = await db.execute(select(Answer).where(Answer.generation_id == gen.id))
        all_answers.extend(ans_result.scalars().all())

    frameworks: dict[str, list[str]] = {"iso-27001": [], "soc-2": [], "gdpr": [], "dora": []}
    for ev in evidence:
        for fw in ev.frameworks or []:
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

    lines.extend(
        [
            "",
            "---",
            "",
            "## 3. Evidence Library",
            "",
        ]
    )

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

    lines.extend(
        [
            "---",
            "",
            "## 4. Policies",
            "",
        ]
    )

    for p in policies:
        lines.append(f"### {p.title}")
        lines.append(f"- **Status:** {p.status}")
        lines.append(f"- **Version:** {p.version}")
        lines.append(f"- **Category:** {p.category}")
        if p.next_review:
            lines.append(f"- **Next Review:** {p.next_review}")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## 5. Penetration Tests",
            "",
        ]
    )

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
                lines.append(
                    f"  - [{f.get('severity', 'N/A').upper()}] {f.get('title', 'Untitled')} — {f.get('status', 'unknown')}"
                )
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## 6. Security Answers",
            "",
        ]
    )

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

    lines.extend(
        [
            "---",
            "",
            "*This report was automatically generated by Verity Trust Copilot.*",
            "*Review all content before sharing with auditors or customers.*",
        ]
    )

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


@router.get("/audit-package")
async def generate_audit_package(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate a complete audit-ready ZIP package with all compliance data."""
    org_id = current_user.org_id
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    evidence_result = await db.execute(select(EvidenceRecord).where(EvidenceRecord.org_id == org_id))
    evidence = evidence_result.scalars().all()

    policies_result = await db.execute(select(Policy).where(Policy.org_id == org_id))
    policies = policies_result.scalars().all()

    pentests_result = await db.execute(select(Pentest).where(Pentest.org_id == org_id))
    pentests = pentests_result.scalars().all()

    gen_result = await db.execute(select(AnswerGeneration).where(AnswerGeneration.org_id == org_id))
    generations = gen_result.scalars().all()

    all_answers = []
    for gen in generations:
        ans_result = await db.execute(select(Answer).where(Answer.generation_id == gen.id))
        all_answers.extend(ans_result.scalars().all())

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Evidence JSON
        evidence_data = []
        for ev in evidence:
            days_ago = (datetime.now(timezone.utc).date() - ev.last_reviewed).days
            evidence_data.append(
                {
                    "id": ev.id,
                    "title": ev.title,
                    "type": ev.type,
                    "frameworks": ev.frameworks,
                    "control_ids": ev.control_ids,
                    "last_reviewed": str(ev.last_reviewed),
                    "owner": ev.owner,
                    "summary": ev.summary,
                    "snippets": ev.snippets,
                    "freshness_days": days_ago,
                    "status": "fresh" if days_ago <= 180 else ("stale" if days_ago <= 365 else "outdated"),
                }
            )
        zf.writestr("evidence.json", json.dumps(evidence_data, indent=2, default=str))

        # Policies JSON
        policies_data = [
            {
                "id": p.id,
                "title": p.title,
                "category": p.category,
                "content": p.content,
                "status": p.status,
                "version": p.version,
                "next_review": str(p.next_review) if p.next_review else None,
            }
            for p in policies
        ]
        zf.writestr("policies.json", json.dumps(policies_data, indent=2, default=str))

        # Pentests JSON
        pentests_data = [
            {
                "id": pt.id,
                "title": pt.title,
                "scope": pt.scope,
                "methodology": pt.methodology,
                "status": pt.status,
                "start_date": str(pt.start_date) if pt.start_date else None,
                "end_date": str(pt.end_date) if pt.end_date else None,
                "findings": pt.findings or [],
            }
            for pt in pentests
        ]
        zf.writestr("pentests.json", json.dumps(pentests_data, indent=2, default=str))

        # Answers JSON
        answers_data = [
            {
                "id": a.id,
                "question": a.question,
                "answer_text": a.answer_text,
                "confidence": a.confidence,
                "needs_human_review": a.needs_human_review,
                "confidence_rationale": a.confidence_rationale,
                "citations": a.citations or [],
                "freshness": a.freshness or [],
            }
            for a in all_answers
        ]
        zf.writestr("answers.json", json.dumps(answers_data, indent=2, default=str))

        # SOC 2 Report (markdown)
        soc2_lines = [
            f"# SOC 2 Type II Compliance Report — {today}",
            "",
            f"Organization ID: {org_id}",
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "---",
            "",
            "## Evidence Library",
            "",
            f"**{len(evidence)} records total**",
            "",
        ]
        for ev in evidence:
            days_ago = (datetime.now(timezone.utc).date() - ev.last_reviewed).days
            status = "Fresh" if days_ago <= 180 else ("Stale" if days_ago <= 365 else "Outdated")
            soc2_lines.append(f"### {ev.title}")
            soc2_lines.append(
                f"- Type: {ev.type}  |  Owner: {ev.owner}  |  Last Reviewed: {ev.last_reviewed} ({days_ago}d — {status})"
            )
            soc2_lines.append(f"- Frameworks: {', '.join(ev.frameworks or []) or 'None'}")
            soc2_lines.append(f"- Summary: {ev.summary}")
            soc2_lines.append("")
            for s in ev.snippets or []:
                soc2_lines.append(f"  > {s}")
            soc2_lines.append("")

        soc2_lines.extend(
            [
                "---",
                "",
                "## Policies",
                "",
            ]
        )
        for p in policies:
            soc2_lines.append(f"### {p.title} (v{p.version} — {p.status})")
            soc2_lines.append(f"- Category: {p.category}")
            if p.content:
                soc2_lines.append(f"  {p.content[:300]}")
            soc2_lines.append("")

        soc2_lines.extend(
            [
                "---",
                "",
                "## Penetration Tests",
                "",
            ]
        )
        for pt in pentests:
            soc2_lines.append(f"### {pt.title} — {pt.status}")
            soc2_lines.append(f"- Scope: {pt.scope}  |  Methodology: {pt.methodology}")
            for f in pt.findings or []:
                soc2_lines.append(
                    f"  - [{f.get('severity', '?').upper()}] {f.get('title', 'Untitled')} ({f.get('status', '?')})"
                )
            soc2_lines.append("")

        soc2_lines.extend(
            [
                "---",
                "",
                "## Security Answers",
                "",
            ]
        )
        for a in all_answers:
            conf = (a.confidence or "unknown").upper()
            review = "NEEDS REVIEW" if a.needs_human_review else "Approved"
            soc2_lines.append(f"### [{conf}] {a.question}")
            soc2_lines.append(f"**Status:** {review}")
            soc2_lines.append(f"{a.answer_text[:400]}{'...' if len(a.answer_text or '') > 400 else ''}")
            soc2_lines.append("")

        zf.writestr("soc2-report.md", "\n".join(soc2_lines))

        # Manifest
        manifest = [
            "# Audit Package Manifest",
            "",
            f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            f"**Organization:** {org_id}",
            "",
            "## Contents",
            "",
            "| File | Description | Records |",
            "|------|-------------|---------|",
            f"| `evidence.json` | All evidence records with freshness status | {len(evidence)} |",
            f"| `policies.json` | Security policies with versions | {len(policies)} |",
            f"| `pentests.json` | Penetration tests with findings | {len(pentests)} |",
            f"| `answers.json` | Generated security answers with confidence | {len(all_answers)} |",
            "| `soc2-report.md` | Human-readable SOC 2 report (markdown) | — |",
            "| `manifest.md` | This file | — |",
            "",
            "---",
            "*Generated by Verity Trust Copilot — review before sharing with auditors.*",
        ]
        zf.writestr("manifest.md", "\n".join(manifest))

    buf.seek(0)

    audit = AuditLog(
        org_id=org_id,
        user_id=current_user.id,
        resource_type="report",
        resource_id="audit-package",
        action="export",
        changes={
            "evidence_count": len(evidence),
            "answers_count": len(all_answers),
            "policies_count": len(policies),
            "pentests_count": len(pentests),
        },
    )
    db.add(audit)
    await db.commit()

    filename = f"audit-package-{today}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
