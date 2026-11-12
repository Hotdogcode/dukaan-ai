"""
Unit of Work (UoW) Pattern for DukaanAI Database Transactions.
Ensures atomic transactional boundaries, automatic rollbacks on errors,
and strict multi-tenant Row-Level Security (RLS) scoping.
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Self
import uuid
from sqlalchemy.orm import Session

from .session import SessionLocal, set_tenant_context


class UnitOfWork:
    """
    Manages a single database session and transaction lifecycle.
    Guarantees that changes are committed atomically or rolled back completely on error.
    """

    def __init__(self, tenant_id: uuid.UUID | None = None, session: Session | None = None) -> None:
        self.tenant_id = tenant_id
        self._external_session = session is not None
        self.session: Session = session if session is not None else SessionLocal()

    def __enter__(self) -> Self:
        if self.tenant_id is not None:
            set_tenant_context(self.session, self.tenant_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()

        if not self._external_session:
            self.session.close()

    def commit(self) -> None:
        """Commits the active transaction."""
        self.session.commit()

    def rollback(self) -> None:
        """Rolls back the active transaction."""
        self.session.rollback()


@contextmanager
def get_unit_of_work(tenant_id: uuid.UUID | None = None) -> Generator[UnitOfWork, None, None]:
    """Context manager yielding a managed UnitOfWork instance."""
    uow = UnitOfWork(tenant_id=tenant_id)
    with uow:
        yield uow
