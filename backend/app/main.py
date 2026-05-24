from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.database import Base, engine
from app.middleware import LoggingMiddleware, setup_logging, setup_security
from app.middleware.license import LicenseMiddleware
from app.routers import answers, approvals, auth, dashboard, evidence, export, health, llm, org, pentests, policies, reports, vanta

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="Verity Trust Copilot", version="0.1.0", lifespan=lifespan)

origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENVIRONMENT)

Instrumentator().instrument(app).expose(app)

app.add_middleware(LoggingMiddleware)
app.add_middleware(LicenseMiddleware)
setup_security(app)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(org.router)
app.include_router(answers.router)
app.include_router(approvals.router)
app.include_router(export.router)
app.include_router(evidence.router)
app.include_router(dashboard.router)
app.include_router(policies.router)
app.include_router(pentests.router)
app.include_router(vanta.router)
app.include_router(reports.router)
app.include_router(llm.router)
