import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import jwt
from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_FILE)


def _get_jwt_config() -> tuple[str, str, int]:
    secret_key = os.getenv("JWT_SECRET_KEY")
    algorithm = os.getenv("JWT_ALGORITHM")
    expire_minutes = os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    if not secret_key or not algorithm or not expire_minutes:
        raise RuntimeError(
            "JWT configuration is incomplete. Check your .env file."
        )

    try:
        expire_minutes_value = int(expire_minutes)
    except ValueError as exc:
        raise RuntimeError(
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be an integer."
        ) from exc

    if expire_minutes_value <= 0:
        raise RuntimeError(
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero."
        )

    return secret_key, algorithm, expire_minutes_value


def create_access_token(subject: str) -> str:
    secret_key, algorithm, expire_minutes = _get_jwt_config()
    issued_at = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": issued_at,
        "exp": issued_at + timedelta(minutes=expire_minutes),
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    secret_key, algorithm, _ = _get_jwt_config()
    return jwt.decode(token, secret_key, algorithms=[algorithm])
