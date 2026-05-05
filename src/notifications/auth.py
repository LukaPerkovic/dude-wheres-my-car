"""HTTP Basic Auth dependency for admin endpoints.

Security notes:
- Basic Auth transmits credentials base64-encoded, NOT encrypted.
- Safe on localhost. On any public deployment, terminate TLS in front
  (ALB + ACM, CloudFront, nginx, etc.) so credentials are encrypted in transit.
- We compare using `secrets.compare_digest` to avoid timing attacks.
"""

from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from src.config import Settings


_security = HTTPBasic()
_settings = Settings()


def require_admin(
    credentials: HTTPBasicCredentials = Depends(_security),
) -> str:
    """FastAPI dependency: rejects unless valid admin credentials are supplied."""
    expected_user = _settings.admin_username.encode("utf-8")
    expected_pass = _settings.admin_password.encode("utf-8")

    supplied_user = credentials.username.encode("utf-8")
    supplied_pass = credentials.password.encode("utf-8")

    user_ok = secrets.compare_digest(supplied_user, expected_user)
    pass_ok = secrets.compare_digest(supplied_pass, expected_pass)

    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username