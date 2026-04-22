import os
from contextlib import contextmanager, asynccontextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./example.db")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
Base = declarative_base()
Session = scoped_session(SessionLocal)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


get_db = contextmanager(get_session)


# Configuration asynchrone
SQLALCHEMY_ASYNC_DATABASE_URL = os.environ.get("DATABASE_ASYNC_URL", "sqlite+aiosqlite:///./example.db")
async_engine = create_async_engine(
    SQLALCHEMY_ASYNC_DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"timeout": 30},
)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_async_session():
    """Async context manager pour les sessions asynchrones"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_async_session_dep() -> AsyncSession:
    """FastAPI dependency — yields a raw AsyncSession."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


get_async_db = asynccontextmanager(get_async_session)  # ty:ignore[no-matching-overload]
