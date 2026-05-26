"""Integration management API — connect, test, monitor cloud/SaaS integrations."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.integration import Integration, ComplianceTest, TestResult
from app.models.user import User
from app.services.integrations import get_provider, list_providers
from app.services.scheduler import run_integration_now

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


@router.get("/providers")
async def get_providers_list(current_user: User = Depends(get_current_active_user)):
    return {"providers": list_providers()}


@router.get("/")
async def list_integrations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Integration).where(Integration.org_id == current_user.org_id).order_by(Integration.created_at.desc())
    )
    integrations = result.scalars().all()
    return [
        {
            "id": i.id,
            "provider": i.provider,
            "name": i.name,
            "enabled": i.enabled,
            "last_run_at": i.last_run_at.isoformat() if i.last_run_at else None,
            "last_status": i.last_status,
            "last_error": i.last_error,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }
        for i in integrations
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_integration(
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    provider_name = body.get("provider", "")
    if provider_name not in {"aws", "github"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider_name}. Use 'aws' or 'github'.",
        )

    name = body.get("name", f"{provider_name.upper()} Integration")
    config = body.get("config", {})

    provider = get_provider(provider_name, config)
    if not provider:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to initialize provider")

    connected = await provider.connect()
    if not connected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Connection failed. Verify your credentials."
        )

    integration = Integration(
        org_id=current_user.org_id,
        provider=provider_name,
        name=name,
        enabled=True,
        config=config,
        last_status="healthy",
    )
    db.add(integration)
    await db.flush()

    for test_def in provider.test_definitions:
        test = ComplianceTest(
            org_id=current_user.org_id,
            integration_id=integration.id,
            name=test_def["name"],
            description=test_def.get("description", ""),
            frameworks=test_def.get("frameworks", []),
            control_ids=test_def.get("control_ids", []),
            category=test_def.get("category", "general"),
        )
        db.add(test)

    await db.commit()
    await db.refresh(integration)

    return {
        "id": integration.id,
        "provider": integration.provider,
        "name": integration.name,
        "enabled": integration.enabled,
        "last_status": integration.last_status,
        "created_at": integration.created_at.isoformat() if integration.created_at else None,
    }


@router.post("/{integration_id}/run")
async def run_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Integration).where(Integration.id == integration_id, Integration.org_id == current_user.org_id)
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")

    await run_integration_now(integration_id)
    return {"status": "triggered", "integration_id": integration_id}


@router.put("/{integration_id}")
async def update_integration(
    integration_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Integration).where(Integration.id == integration_id, Integration.org_id == current_user.org_id)
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")

    allowed = {"name", "enabled", "config"}
    for key, value in body.items():
        if key in allowed:
            setattr(integration, key, value)

    await db.commit()
    return {"id": integration.id, "status": "updated"}


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Integration).where(Integration.id == integration_id, Integration.org_id == current_user.org_id)
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")

    await db.delete(integration)
    await db.commit()


@router.get("/{integration_id}/results")
async def get_test_results(
    integration_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Integration).where(Integration.id == integration_id, Integration.org_id == current_user.org_id)
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")

    results_result = await db.execute(
        select(TestResult)
        .where(TestResult.integration_id == integration_id)
        .order_by(TestResult.created_at.desc())
        .limit(limit)
    )
    results = results_result.scalars().all()

    tests_result = await db.execute(select(ComplianceTest).where(ComplianceTest.integration_id == integration_id))
    tests = {t.id: t.name for t in tests_result.scalars().all()}

    return {
        "integration_id": integration_id,
        "results": [
            {
                "id": r.id,
                "test_name": tests.get(r.test_id, "Unknown"),
                "status": r.status,
                "message": r.message,
                "evidence": r.evidence,
                "resources_checked": r.resources_checked,
                "resources_failed": r.resources_failed,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in results
        ],
    }


@router.get("/dashboard/summary")
async def integration_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    integrations_result = await db.execute(select(Integration).where(Integration.org_id == current_user.org_id))
    integrations = integrations_result.scalars().all()

    total = len(integrations)
    healthy = sum(1 for i in integrations if i.last_status == "healthy")
    degraded = sum(1 for i in integrations if i.last_status == "degraded")
    error = sum(1 for i in integrations if i.last_status == "error")
    pending = sum(1 for i in integrations if i.last_status == "pending")

    recent_result = await db.execute(
        select(TestResult)
        .where(TestResult.org_id == current_user.org_id)
        .order_by(TestResult.created_at.desc())
        .limit(20)
    )
    recent = recent_result.scalars().all()

    return {
        "integrations": {"total": total, "healthy": healthy, "degraded": degraded, "error": error, "pending": pending},
        "recent_results": [
            {
                "id": r.id,
                "status": r.status,
                "message": r.message,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in recent
        ],
    }
