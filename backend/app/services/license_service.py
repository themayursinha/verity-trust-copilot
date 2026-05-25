"""License key validation using Ed25519 signatures."""

import base64
import json
import time
from dataclasses import dataclass
from typing import Optional

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

from app.config import settings


@dataclass
class LicenseInfo:
    org_id: str
    org_name: str
    max_seats: int
    issued_at: int
    expires_at: Optional[int]
    customer_email: str
    valid: bool
    reason: str = ""


def _load_public_key() -> Optional[bytes]:
    if not settings.LICENSE_PUBLIC_KEY:
        return None
    try:
        return base64.b64decode(settings.LICENSE_PUBLIC_KEY)
    except Exception:
        return None


def validate_license(license_key: str) -> LicenseInfo:
    """Validate a license key and return the decoded license info."""
    public_key = _load_public_key()

    if not public_key:
        return LicenseInfo(
            org_id="free",
            org_name="Free Tier",
            max_seats=settings.LICENSE_FREE_SEATS,
            issued_at=0,
            expires_at=None,
            customer_email="",
            valid=True,
            reason="No license key configured — free tier active",
        )

    try:
        parts = license_key.split(".")
        if len(parts) != 2:
            return LicenseInfo(
                org_id="",
                org_name="",
                max_seats=0,
                issued_at=0,
                expires_at=None,
                customer_email="",
                valid=False,
                reason="Invalid license key format",
            )

        payload_b64, signature_b64 = parts
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + "===")
        signature_bytes = base64.urlsafe_b64decode(signature_b64 + "===")

        verify_key = VerifyKey(public_key)
        verify_key.verify(payload_bytes, signature_bytes)

        payload = json.loads(payload_bytes.decode())

        expires_at = payload.get("exp")
        if expires_at and expires_at < int(time.time()):
            return LicenseInfo(
                org_id=payload.get("org_id", ""),
                org_name=payload.get("org_name", ""),
                max_seats=payload.get("max_seats", 0),
                issued_at=payload.get("iat", 0),
                expires_at=expires_at,
                customer_email=payload.get("email", ""),
                valid=False,
                reason="License has expired",
            )

        return LicenseInfo(
            org_id=payload.get("org_id", ""),
            org_name=payload.get("org_name", ""),
            max_seats=payload.get("max_seats", 0),
            issued_at=payload.get("iat", 0),
            expires_at=expires_at,
            customer_email=payload.get("email", ""),
            valid=True,
            reason="",
        )

    except BadSignatureError:
        return LicenseInfo(
            org_id="",
            org_name="",
            max_seats=0,
            issued_at=0,
            expires_at=None,
            customer_email="",
            valid=False,
            reason="Invalid license signature — key may be tampered",
        )
    except Exception as e:
        return LicenseInfo(
            org_id="",
            org_name="",
            max_seats=0,
            issued_at=0,
            expires_at=None,
            customer_email="",
            valid=False,
            reason=f"License validation error: {str(e)}",
        )


def get_active_seat_limit(license_info: LicenseInfo) -> int:
    """Return the current active seat limit."""
    if license_info.valid:
        return license_info.max_seats
    return settings.LICENSE_FREE_SEATS
