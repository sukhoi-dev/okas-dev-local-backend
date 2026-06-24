import hashlib
import secrets
from random import SystemRandom


def generate_otp() -> str:
    return f"{SystemRandom().randint(0, 999999):06d}"


def hash_value(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)
