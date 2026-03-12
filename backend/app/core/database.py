"""TravManager — Async Database Setup"""
from sqlalchemy import Enum as _SAEnum
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def PgEnum(enum_class, pg_type_name):
    """Create an SAEnum that uses enum .value (lowercase) matching PostgreSQL enum types."""
    return _SAEnum(
        enum_class, name=pg_type_name, create_type=False,
        values_callable=lambda e: [m.value for m in e],
    )


async def get_session():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    from app.core.migrate import run_migrations
    async with engine.begin() as conn:
        await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    print("Database connected.")
    # Run SQL migrations (idempotent — safe to run on every startup)
    await run_migrations(engine)
    print("Migrations applied.")


async def close_db():
    await engine.dispose()
    print("Database disconnected.")
