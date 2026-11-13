"""
Security, Cryptography, JWT Token Operations, and Role-Based Permissions for DukaanAI.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Any
import uuid
import bcrypt
import jwt

from .config import settings
from .exceptions import AuthenticationRequired, InsufficientPermissions


# -----------------------------------------------------------------------------
# Role and Granular Permission Definitions
# -----------------------------------------------------------------------------
class Permissions:
    BUSINESS_READ = "business.read"
    BUSINESS_UPDATE = "business.update"
    MEMBERS_MANAGE = "members.manage"
    PRODUCTS_READ = "products.read"
    PRODUCTS_WRITE = "products.write"
    PRODUCTS_CREATE = "products.create"
    PRODUCTS_UPDATE = "products.update"
    PRODUCTS_DEACTIVATE = "products.deactivate"
    CATEGORIES_MANAGE = "categories.manage"
    BRANDS_MANAGE = "brands.manage"
    SALES_READ = "sales.read"
    SALES_CREATE = "sales.create"
    INVENTORY_READ = "inventory.read"
    INVENTORY_ADJUST = "inventory.adjust"
    INVENTORY_OPENING_STOCK = "inventory.opening_stock"
    INVENTORY_COUNT = "inventory.count"
    INVENTORY_RECONCILE = "inventory.reconcile"
    FINANCE_READ = "finance.read"
    REPORTS_READ = "reports.read"


ROLE_PERMISSIONS: dict[str, set[str]] = {
    "OWNER": {
        Permissions.BUSINESS_READ,
        Permissions.BUSINESS_UPDATE,
        Permissions.MEMBERS_MANAGE,
        Permissions.PRODUCTS_READ,
        Permissions.PRODUCTS_WRITE,
        Permissions.PRODUCTS_CREATE,
        Permissions.PRODUCTS_UPDATE,
        Permissions.PRODUCTS_DEACTIVATE,
        Permissions.CATEGORIES_MANAGE,
        Permissions.BRANDS_MANAGE,
        Permissions.SALES_READ,
        Permissions.SALES_CREATE,
        Permissions.INVENTORY_READ,
        Permissions.INVENTORY_ADJUST,
        Permissions.INVENTORY_OPENING_STOCK,
        Permissions.INVENTORY_COUNT,
        Permissions.INVENTORY_RECONCILE,
        Permissions.FINANCE_READ,
        Permissions.REPORTS_READ,
    },
    "MANAGER": {
        Permissions.BUSINESS_READ,
        Permissions.BUSINESS_UPDATE,
        Permissions.MEMBERS_MANAGE,
        Permissions.PRODUCTS_READ,
        Permissions.PRODUCTS_WRITE,
        Permissions.PRODUCTS_CREATE,
        Permissions.PRODUCTS_UPDATE,
        Permissions.PRODUCTS_DEACTIVATE,
        Permissions.CATEGORIES_MANAGE,
        Permissions.BRANDS_MANAGE,
        Permissions.SALES_READ,
        Permissions.SALES_CREATE,
        Permissions.INVENTORY_READ,
        Permissions.INVENTORY_ADJUST,
        Permissions.INVENTORY_OPENING_STOCK,
        Permissions.INVENTORY_COUNT,
        Permissions.INVENTORY_RECONCILE,
        Permissions.FINANCE_READ,
        Permissions.REPORTS_READ,
    },
    "CASHIER": {
        Permissions.BUSINESS_READ,
        Permissions.PRODUCTS_READ,
        Permissions.SALES_READ,
        Permissions.SALES_CREATE,
        Permissions.FINANCE_READ,
        Permissions.INVENTORY_READ,
    },
    "INVENTORY_STAFF": {
        Permissions.BUSINESS_READ,
        Permissions.PRODUCTS_READ,
        Permissions.PRODUCTS_WRITE,
        Permissions.PRODUCTS_CREATE,
        Permissions.PRODUCTS_UPDATE,
        Permissions.CATEGORIES_MANAGE,
        Permissions.BRANDS_MANAGE,
        Permissions.INVENTORY_READ,
        Permissions.INVENTORY_ADJUST,
        Permissions.INVENTORY_COUNT,
    },
}


def get_role_permissions(role: str) -> set[str]:
    """Returns the set of granted permissions for a given business role."""
    return ROLE_PERMISSIONS.get(role.upper(), set())


def check_permission(user_role: str, required_permission: str) -> bool:
    """Evaluates whether the user's role satisfies the required permission."""
    granted = get_role_permissions(user_role)
    return required_permission in granted


# -----------------------------------------------------------------------------
# Cryptographic and Token Utilities
# -----------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt with salt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def hash_token(raw_token: str) -> str:
    """
    Creates a deterministic SHA-256 digest of a raw token (e.g. refresh token).
    Used for safe persistence in the database so leaks do not compromise active sessions.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_secure_token(length_bytes: int = 32) -> str:
    """Generates a cryptographically secure random URL-safe token."""
    return secrets.token_urlsafe(length_bytes)


# -----------------------------------------------------------------------------
# JWT Operations
# -----------------------------------------------------------------------------
def create_access_token(user_id: uuid.UUID, session_id: uuid.UUID) -> str:
    """
    Creates a signed, short-lived JWT access token.
    Contains minimal claims: subject (user_id), session_id, jti, exp, iat, iss, aud.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "session_id": str(session_id),
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decodes and validates a JWT access token signature, issuer, audience, and expiration.
    Raises AuthenticationRequired if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationRequired("Access token has expired. Please refresh your session.")
    except jwt.InvalidTokenError as e:
        raise AuthenticationRequired(f"Invalid access token: {str(e)}")
