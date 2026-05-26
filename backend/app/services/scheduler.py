"""Background task scheduler for continuous integration checks."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, update

from app.database import async_session_maker
from app.models.integration import Integration, ComplianceTest, TestResult
from app.services.integrations import get_provider

logger = logging.getLogger("verity.scheduler")

scheduler = AsyncIOScheduler()


async def _run_integration_check(integration_id: str):
    async with async_session_maker() as db:
        result = await db.execute(select(Integration).where(Integration.id == integration_id))
        integration = result.scalar_one_or_none()
        if not integration or not integration.enabled:
            return

        provider = get_provider(integration.provider, integration.config or {})
        if not provider:
            await db.execute(
                update(Integration)
                .where(Integration.id == integration_id)
                .values(last_status="error", last_error=f"Unknown provider: {integration.provider}")
            )
            await db.commit()
            return

        connected = await provider.connect()
        if not connected:
            await db.execute(
                update(Integration)
                .where(Integration.id == integration_id)
                .values(last_status="error", last_error="Connection failed — check credentials")
            )
            await db.commit()
            return

        results = await provider.run_all_tests()

        tests_result = await db.execute(
            select(ComplianceTest).where(
                ComplianceTest.integration_id == integration_id, ComplianceTest.enabled.is_(True)
            )
        )
        existing_tests = {t.name: t for t in tests_result.scalars().all()}

        for result in results:
            if result.test_name not in existing_tests:
                test = ComplianceTest(
                    org_id=integration.org_id,
                    integration_id=integration_id,
                    name=result.test_name,
                    category="auto-detected",
                )
                db.add(test)
                await db.flush()
                test_id = test.id
            else:
                test_id = existing_tests[result.test_name].id

            tr = TestResult(
                org_id=integration.org_id,
                test_id=test_id,
                integration_id=integration_id,
                status=result.status,
                evidence=result.evidence,
                message=result.message,
                resources_checked=result.resources_checked,
                resources_failed=result.resources_failed,
            )
            db.add(tr)

        passed = sum(1 for r in results if r.status == "pass")
        failed = sum(1 for r in results if r.status == "fail")
        errors = sum(1 for r in results if r.status == "error")

        status = "healthy" if failed == 0 and errors == 0 else ("degraded" if failed > 0 else "error")
        await db.execute(
            update(Integration)
            .where(Integration.id == integration_id)
            .values(
                last_status=status,
                last_error=None,
                last_run_at=select(TestResult.created_at)
                .where(TestResult.integration_id == integration_id)
                .order_by(TestResult.created_at.desc())
                .limit(1)
                .scalar_subquery(),
            )
        )

        await db.commit()
        logger.info(
            f"Integration {integration.provider}/{integration_id}: {passed} pass, {failed} fail, {errors} errors"
        )


def start_scheduler():
    scheduler.add_job(_run_all_integrations, "interval", hours=1, id="integration_checks", replace_existing=True)
    scheduler.start()
    logger.info("Integration scheduler started — running checks every 1 hour")


async def _run_all_integrations():
    async with async_session_maker() as db:
        result = await db.execute(select(Integration).where(Integration.enabled.is_(True)))
        integrations = result.scalars().all()
        for integration in integrations:
            await _run_integration_check(integration.id)


async def run_integration_now(integration_id: str):
    await _run_integration_check(integration_id)
