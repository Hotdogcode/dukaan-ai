"""
Test configuration, database fixtures, and HTTP client fixtures for DukaanAI test suite.
"""

import os
from collections.abc import AsyncGenerator, Generator
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.config import settings
from backend.app.infrastructure.database.base import Base
import backend.app.infrastructure.database.models  # Registers all 43 models
from backend.app.infrastructure.database.session import get_db_session
from backend.app.infrastructure.otp.dev_provider import DevOTPProvider
from backend.app.infrastructure.otp.service import OTPService
from backend.app.main import app

# Determine test database: Use TEST_DATABASE_URL if configured, otherwise SQLite in-memory with StaticPool
TEST_DB_URL = settings.TEST_DATABASE_URL or "sqlite:///:memory:"
connect_args = {"check_same_thread": False} if "sqlite" in TEST_DB_URL else {}

test_engine = create_engine(
    TEST_DB_URL,
    connect_args=connect_args,
    poolclass=StaticPool if "sqlite" in TEST_DB_URL else None,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Initializes schema once for test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def clean_otp_storage():
    """Resets in-memory OTP storage before each test."""
    original_provider = settings.OTP_PROVIDER
    settings.OTP_PROVIDER = "dev"
    OTPService.clear_all()
    OTPService._provider_instance = DevOTPProvider()
    yield
    settings.OTP_PROVIDER = original_provider


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provides a fresh transactional database session for each test function."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
async def client(db_session: Session) -> AsyncGenerator[AsyncClient, None]:
    """Provides an asynchronous HTTP test client with database dependency override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
