"""
Unit Tests for Cryptography, JWT Tokens, and Role-Based Permissions.
"""

from datetime import datetime, timedelta, timezone
import uuid
import jwt
import pytest

from backend.app.core.config import settings
from backend.app.core.exceptions import AuthenticationRequired
from backend.app.core.security import (
    Permissions,
    check_permission,
    create_access_token,
    decode_access_token,
    generate_secure_token,
    get_role_permissions,
    hash_password,
    hash_token,
    verify_password,
)


def test_password_hashing_and_verification():
    """Verify bcrypt salt hashing and constant-time verification."""
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_token_hashing_is_deterministic():
    """Verify SHA-256 token hashing produces consistent digests."""
    raw_token = generate_secure_token(32)
    digest1 = hash_token(raw_token)
    digest2 = hash_token(raw_token)

    assert digest1 == digest2
    assert len(digest1) == 64  # SHA-256 hex length


def test_jwt_access_token_creation_and_decoding():
    """Verify JWT access token encodes claims and decodes cleanly."""
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()

    token = create_access_token(user_id=user_id, session_id=session_id)
    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["session_id"] == str(session_id)
    assert payload["iss"] == settings.JWT_ISSUER
    assert payload["aud"] == settings.JWT_AUDIENCE
    assert "jti" in payload
    assert payload["exp"] > payload["iat"]


def test_expired_jwt_raises_authentication_required():
    """Verify expired tokens are rejected with AuthenticationRequired."""
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    expired_time = now - timedelta(minutes=5)

    expired_payload = {
        "sub": str(user_id),
        "session_id": str(session_id),
        "jti": str(uuid.uuid4()),
        "iat": int((now - timedelta(minutes=10)).timestamp()),
        "exp": int(expired_time.timestamp()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    }
    expired_token = jwt.encode(expired_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(AuthenticationRequired) as exc_info:
        decode_access_token(expired_token)
    assert "expired" in str(exc_info.value).lower()


def test_role_based_permissions():
    """Verify role-to-permission mapping and hierarchy."""
    # OWNER has all permissions
    assert check_permission("OWNER", Permissions.BUSINESS_UPDATE) is True
    assert check_permission("OWNER", Permissions.MEMBERS_MANAGE) is True
    assert check_permission("OWNER", Permissions.SALES_CREATE) is True

    # CASHIER has sales and POS permissions, but NOT members.manage or business.update
    assert check_permission("CASHIER", Permissions.SALES_CREATE) is True
    assert check_permission("CASHIER", Permissions.BUSINESS_READ) is True
    assert check_permission("CASHIER", Permissions.MEMBERS_MANAGE) is False
    assert check_permission("CASHIER", Permissions.BUSINESS_UPDATE) is False

    # INVENTORY_STAFF has inventory permissions, but NOT finance.read or sales.create
    assert check_permission("INVENTORY_STAFF", Permissions.INVENTORY_ADJUST) is True
    assert check_permission("INVENTORY_STAFF", Permissions.FINANCE_READ) is False
    assert check_permission("INVENTORY_STAFF", Permissions.SALES_CREATE) is False
