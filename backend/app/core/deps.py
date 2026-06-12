"""
FastAPI dependency functions shared across routers.

get_current_user is the core auth guard — inject it into any route that
requires authentication: async def my_route(user = Depends(get_current_user))
"""
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Auth dependency. Does three things in order:
    1. Decodes and validates the JWT signature and expiry
    2. Checks Redis blacklist — rejects if the token was logged out
    3. Loads the user from PostgreSQL

    If any step fails, raises HTTP 401.
    """
    token = credentials.credentials

    # Step 1: validate signature and expiry
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    jti: str | None = payload.get("jti")
    user_id_str: str | None = payload.get("sub")

    if not jti or not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload",
        )

    # Step 2: check Redis blacklist
    is_blacklisted = await request.app.state.redis.get(f"blacklist:{jti}")
    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    # Step 3: load user from DB
    try:
        user_uuid = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        )

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user