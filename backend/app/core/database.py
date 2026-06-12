"""
Async SQLAlchemy engine and session factory.

Why async: FastAPI is built on async Python (ASGI). Using async DB sessions
means DB queries don't block other requests while waiting for PostgreSQL.
asyncpg is the async PostgreSQL driver — much faster than psycopg2 under load.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,       # Set True to log every SQL query — useful for debugging
    pool_pre_ping=True,  # Test connections before using them; handles DB restarts
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevents lazy-loading errors after await session.commit()
)


class Base(DeclarativeBase):
    """Base class all SQLAlchemy models inherit from."""
    pass


async def get_db():
    """
    FastAPI dependency that yields a database session.
    The session is committed on success and rolled back on any exception.
    The 'async with' block ensures the session is always closed.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise