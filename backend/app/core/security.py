"""
Password hashing and JWT token utilities.

Why bcrypt directly (not passlib): passlib 1.7.4 has known compatibility
warnings with bcrypt >= 4.0. Using bcrypt directly removes the dependency.

Why JWT with JTI: JTI (JWT ID) is a unique identifier per token.
On logout, we store the JTI in Redis with a TTL matching the token's
remaining lifetime. This lets us invalidate specific tokens without
invalidating all tokens for a user.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import jwt

from app.core.config import settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt. rounds=12 is the security/speed balance."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.
    bcrypt.checkpw is timing-safe — takes the same time regardless of where
    the comparison fails, preventing timing attacks.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(subject: str) -> tuple[str, str]:
    """
    Create a signed JWT token.

    Returns (token_string, jti) where jti is the unique token ID used for blacklisting.

    The payload contains:
      sub  — user ID (subject)
      jti  — unique token ID (for revocation)
      exp  — expiry timestamp
      iat  — issued at timestamp
    """
    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)

    payload: dict[str, Any] = {
        "sub": subject,
        "jti": jti,
        "exp": expire,
        "iat": now,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token, jti


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token. Raises jose.JWTError if:
    - signature is invalid
    - token is expired
    - token is malformed
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])