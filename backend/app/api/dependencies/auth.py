"""
FastAPI Security and Tenant Resolution Dependencies for DukaanAI.
Handles JWT token authentication, authoritative business membership verification,
and automatic transaction-scoped Row-Level Security (RLS) enforcement.
"""

from collections.abc import Callable
import uuid
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    AuthenticationRequired,
    BusinessAccessDenied,
    InsufficientPermissions,
    SessionRevoked,
    UserNotFound,
    UserSuspended,
)
from backend.app.core.logging import set_log_context
from backend.app.core.security import check_permission, decode_access_token
from backend.app.infrastructure.database.models import BusinessUser, RefreshSession, User
from backend.app.infrastructure.database.session import get_db_session, set_tenant_context

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: Session = Depends(get_db_session),
) -> User:
    """
    Validates JWT bearer token, checks session liveness in refresh_sessions,
    and returns the authenticated User entity.
    """
    if credentials is None or not credentials.credentials:
        raise AuthenticationRequired("Missing or malformed Authorization header.")

    token = credentials.credentials
    payload = decode_access_token(token)

    user_id_str = payload.get("sub")
    session_id_str = payload.get("session_id")
    if not user_id_str or not session_id_str:
        raise AuthenticationRequired("Invalid token claims: missing subject or session ID.")

    try:
        user_id = uuid.UUID(user_id_str)
        session_id = uuid.UUID(session_id_str)
    except ValueError:
        raise AuthenticationRequired("Invalid token claims: non-UUID identifiers.")

    # Authoritative session liveness check
    session_record = db.get(RefreshSession, session_id)
    if not session_record or session_record.revoked_at is not None:
        raise SessionRevoked("Your login session has expired or been revoked. Please sign in again.")

    # Retrieve active user
    user = db.get(User, user_id)
    if not user:
        raise UserNotFound()

    if not user.is_active:
        raise UserSuspended("This account is suspended or disabled.")

    # Enrich request context for structured logging
    set_log_context(user_id=str(user.id))
    return user


def get_tenant_membership(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> BusinessUser:
    """
    Authoritative server-side verification of business membership.
    Enforces PostgreSQL Row-Level Security (RLS) on the active transaction session.
    """
    stmt = select(BusinessUser).where(
        BusinessUser.business_id == business_id,
        BusinessUser.user_id == current_user.id,
        BusinessUser.is_active == True,  # noqa: E712
    )
    membership = db.scalar(stmt)
    if not membership:
        raise BusinessAccessDenied("You are not an active member of this business.")

    # Activate transaction-scoped PostgreSQL Row-Level Security (RLS)
    set_tenant_context(db, business_id)
    set_log_context(business_id=str(business_id))

    return membership


def require_permission(permission: str) -> Callable:
    """
    Dependency factory verifying that the authenticated caller has the
    required permission within the target business.
    """

    def permission_checker(
        membership: BusinessUser = Depends(get_tenant_membership),
    ) -> BusinessUser:
        if not check_permission(membership.role, permission):
            raise InsufficientPermissions(permission)
        return membership

    return permission_checker
