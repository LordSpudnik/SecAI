"""
Authentication endpoints: register, login, logout, me.

Note on logout: we decode the token a second time to extract JTI and exp.
This is safe because get_current_user already validated the token — we're
just reading values from a token we know is legitimate.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Register a new user.
    Checks for duplicate email first — fails fast with 409 before hashing.
    bcrypt is intentionally slow (that's the point), so we avoid calling it
    on duplicate emails.
    """
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        id=uuid.uuid4(),
        email=body.email,
        full_name=body.full_name,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    # flush() writes to DB within the open transaction without committing.
    # get_db() commits after the route returns successfully.
    await db.flush()

    return {"message": "Registered successfully"}


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Login with email and password.
    Always returns the same generic error whether the email doesn't exist
    or the password is wrong — prevents user enumeration attacks.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    # verify_password is called even if user is None to prevent timing attacks.
    # If user is None, we verify against a dummy hash so response time is consistent.
    dummy_hash = "$2b$12$dummyhashtopreventtimingattacksonnonexistentusers........."
    password_valid = verify_password(
        body.password,
        user.password_hash if user else dummy_hash,
    )

    if not user or not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token, _ = create_access_token(subject=str(user.id))

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Logout: adds the token's JTI to the Redis blacklist.
    TTL is set to the token's remaining lifetime so Redis auto-cleans it.
    After this, any request with this token gets HTTP 401.
    """
    # Token already validated by get_current_user — safe to decode again
    raw_token = request.headers["authorization"].split(" ")[1]
    payload = decode_token(raw_token)

    jti: str = payload["jti"]
    exp: int = payload["exp"]

    # TTL = seconds remaining until token naturally expires
    now = datetime.now(timezone.utc).timestamp()
    ttl = max(int(exp - now), 1)

    await request.app.state.redis.setex(f"blacklist:{jti}", ttl, "1")

    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the authenticated user's profile data."""
    return UserResponse.model_validate(current_user)