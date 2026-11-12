"""
Security and Multi-Tenant Isolation Tests for DukaanAI.
Verifies cross-tenant isolation, role permission boundaries, and membership enforcement.
"""

import uuid
import pytest
from httpx import AsyncClient

from backend.app.infrastructure.otp.dev_provider import DevOTPProvider
from backend.app.infrastructure.otp.service import OTPService


async def get_user_token(client: AsyncClient, phone: str, name: str) -> str:
    """Helper to authenticate a user."""
    await client.post("/api/v1/auth/request-otp", json={"phone_number": phone})
    provider = OTPService.get_provider()
    assert isinstance(provider, DevOTPProvider)
    otp = provider.get_latest_otp(f"+91{phone}")

    resp = await client.post(
        "/api/v1/auth/verify-otp",
        json={"phone_number": phone, "otp": otp, "full_name": name},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_cross_tenant_isolation_enforced(client: AsyncClient):
    """User A (Business A) cannot view, update, or manage members of Business B."""
    # 1. User A creates Business A
    token_a = await get_user_token(client, "9000000001", "Merchant A")
    resp_a = await client.post(
        "/api/v1/businesses",
        json={"name": "Merchant A Store"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    business_a_id = resp_a.json()["business"]["id"]

    # 2. User B creates Business B
    token_b = await get_user_token(client, "9000000002", "Merchant B")
    resp_b = await client.post(
        "/api/v1/businesses",
        json={"name": "Merchant B Store"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    business_b_id = resp_b.json()["business"]["id"]

    # 3. User B attempts to access Business A -> 403 Forbidden
    unauth_detail = await client.get(
        f"/api/v1/businesses/{business_a_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert unauth_detail.status_code == 403
    assert unauth_detail.json()["error"]["code"] == "BUSINESS_ACCESS_DENIED"

    # 4. User B attempts to update Business A -> 403 Forbidden
    unauth_patch = await client.patch(
        f"/api/v1/businesses/{business_a_id}",
        json={"name": "Hacked Store Name"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert unauth_patch.status_code == 403

    # 5. User B attempts to view members of Business A -> 403 Forbidden
    unauth_members = await client.get(
        f"/api/v1/businesses/{business_a_id}/members",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert unauth_members.status_code == 403


@pytest.mark.asyncio
async def test_cashier_role_restrictions(client: AsyncClient):
    """Staff with CASHIER role cannot update business or add staff members."""
    # Owner creates business
    owner_token = await get_user_token(client, "9000000010", "Store Owner")
    resp = await client.post(
        "/api/v1/businesses",
        json={"name": "Sharma General Store"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    business_id = resp.json()["business"]["id"]

    # Owner adds Cashier
    cashier_phone = "9000000011"
    await client.post(
        f"/api/v1/businesses/{business_id}/members",
        json={"phone_number": cashier_phone, "full_name": "Cashier Rahul", "role": "CASHIER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # Cashier logs in
    cashier_token = await get_user_token(client, cashier_phone, "Cashier Rahul")
    cashier_headers = {"Authorization": f"Bearer {cashier_token}"}

    # Cashier attempts to update business -> 403 Insufficient Permissions
    patch_resp = await client.patch(
        f"/api/v1/businesses/{business_id}",
        json={"name": "Unauthorized Rename"},
        headers=cashier_headers,
    )
    assert patch_resp.status_code == 403
    assert patch_resp.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    # Cashier attempts to add another staff member -> 403 Insufficient Permissions
    add_resp = await client.post(
        f"/api/v1/businesses/{business_id}/members",
        json={"phone_number": "9000000012", "full_name": "Another Cashier", "role": "CASHIER"},
        headers=cashier_headers,
    )
    assert add_resp.status_code == 403
    assert add_resp.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"


@pytest.mark.asyncio
async def test_multiple_businesses_per_user(client: AsyncClient):
    """A user can own or belong to multiple businesses and switch context."""
    user_token = await get_user_token(client, "9000000020", "Serial Retailer")
    headers = {"Authorization": f"Bearer {user_token}"}

    # Register Shop 1
    resp1 = await client.post(
        "/api/v1/businesses",
        json={"name": "Retail Shop 1"},
        headers=headers,
    )
    assert resp1.status_code == 201
    biz1_id = resp1.json()["business"]["id"]

    # Register Shop 2
    resp2 = await client.post(
        "/api/v1/businesses",
        json={"name": "Retail Shop 2"},
        headers=headers,
    )
    assert resp2.status_code == 201
    biz2_id = resp2.json()["business"]["id"]

    # List businesses -> both must be returned
    list_resp = await client.get("/api/v1/businesses", headers=headers)
    assert list_resp.status_code == 200
    ids = {b["business"]["id"] for b in list_resp.json()}
    assert biz1_id in ids
    assert biz2_id in ids
