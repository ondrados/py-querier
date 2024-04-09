import uuid

import pytest_asyncio

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import Base


@pytest_asyncio.fixture(scope="session")
async def test_client():
    async with AsyncClient(app=app, base_url="http://localhost:8000", headers={
        "Authorization": "Token secret"
    }) as client:
        yield client


@pytest_asyncio.fixture(scope="function", autouse=True)
async def test_engine(monkeypatch):
    random_db_name = f"test_{uuid.uuid4().hex[:8]}.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///./{random_db_name}")
    monkeypatch.setattr("app.db.engine", engine)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine


@pytest_asyncio.fixture(scope="function", autouse=True)
async def db_session(monkeypatch, test_engine):
    async_session = sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    monkeypatch.setattr("app.db.async_session", async_session)

    async with async_session() as session:
        async with session.begin():
            try:
                yield session
            finally:
                await session.close()
