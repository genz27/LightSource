"""Async SQLAlchemy engine/session setup."""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from app.models.base import Base
from app.services.persistence import ensure_default_providers
import asyncio
import asyncpg

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.db_dsn.replace("postgresql+psycopg2", "postgresql+asyncpg"),
    echo=False,
    future=True,
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def ensure_database_and_schema() -> None:
    url = make_url(settings.db_dsn)
    target_db = url.database
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        try:
            conn = await asyncpg.connect(
                host=url.host or "127.0.0.1",
                port=url.port or 5432,
                user=url.username or "postgres",
                password=url.password or None,
                database="postgres",
            )
            try:
                await conn.execute(f'CREATE DATABASE "{target_db}"')
            finally:
                await conn.close()
        except Exception:
            pass
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            await conn.execute(text("ALTER TABLE jobs ALTER COLUMN error TYPE TEXT"))
        except Exception:
            try:
                await conn.execute(text("ALTER TABLE public.jobs ALTER COLUMN error TYPE TEXT"))
            except Exception:
                pass
        for stmt in (
            "ALTER TABLE assets ALTER COLUMN url TYPE TEXT",
            "ALTER TABLE assets ALTER COLUMN preview_url TYPE TEXT",
        ):
            try:
                await conn.execute(text(stmt))
            except Exception:
                try:
                    await conn.execute(text(stmt.replace("assets", "public.assets")))
                except Exception:
                    pass
    try:
        async with SessionLocal() as s:
            await ensure_default_providers(s)
    except Exception:
        pass
