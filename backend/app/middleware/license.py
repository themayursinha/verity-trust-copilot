"""License middleware for seat enforcement."""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class LicenseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        return await call_next(request)
