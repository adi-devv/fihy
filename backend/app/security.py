import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt

from .config import get_settings

ALGORITHM = "HS256"


class TokenInvalid(Exception):
    pass


def _create(subject: str, token_type: str, ttl_seconds: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "typ": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, get_settings().secret_key, algorithm=ALGORITHM)


def create_access_token(user_id: str) -> tuple[str, int]:
    ttl = get_settings().access_token_ttl_seconds
    return _create(user_id, "access", ttl), ttl


def create_refresh_token(user_id: str) -> str:
    return _create(user_id, "refresh", get_settings().refresh_token_ttl_seconds)


def read_token(token: str, expected_type: str) -> str:
    try:
        payload = jwt.decode(
            token, get_settings().secret_key, algorithms=[ALGORITHM]
        )
    except jwt.PyJWTError as exc:
        raise TokenInvalid("Your session has expired. Sign in again.") from exc
    if payload.get("typ") != expected_type:
        raise TokenInvalid("Your session has expired. Sign in again.")
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise TokenInvalid("Your session has expired. Sign in again.")
    return subject


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(phone: str, code: str) -> str:
    message = f"{phone}:{code}".encode()
    return hmac.new(
        get_settings().secret_key.encode(), message, hashlib.sha256
    ).hexdigest()


def otp_matches(phone: str, code: str, code_hash: str) -> bool:
    return hmac.compare_digest(hash_otp(phone, code), code_hash)
