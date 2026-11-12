import uuid
from collections.abc import Generator
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings

# Engine setup
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def set_tenant_context(session: Session, tenant_id: uuid.UUID) -> None:
    """
    Sets the transaction-scoped tenant context for Row-Level Security (RLS).
    Uses SET LOCAL so that the setting is strictly scoped to the active transaction
    and automatically cleared upon COMMIT or ROLLBACK, preventing connection pool leaks.
    """
    # Validate UUID format
    val = str(uuid.UUID(str(tenant_id)))
    # PostgreSQL SET LOCAL is transaction-scoped
    bind = getattr(session, "bind", None)
    if bind is None and hasattr(session, "get_bind"):
        try:
            bind = session.get_bind()
        except Exception:
            bind = None

    if bind is not None and getattr(bind, "dialect", None) and bind.dialect.name == "postgresql":
        session.execute(text("SET LOCAL app.current_tenant_id = :tenant_id"), {"tenant_id": val})
    elif bind is None:
        # Fallback for mock sessions in testing
        session.execute(text("SET LOCAL app.current_tenant_id = :tenant_id"), {"tenant_id": val})


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def tenant_session(tenant_id: uuid.UUID) -> Generator[Session, None, None]:
    """Context manager for running database operations under a verified tenant context."""
    session = SessionLocal()
    try:
        set_tenant_context(session, tenant_id)
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
