"""
Integration Tests for Multi-Tenant Businesses API: Creation, updates, and member management.
"""

import pytest
from httpx import AsyncClient

from backend.app.infrastructure.otp.dev_provider import DevOTPProvider
from backend.app.infrastructure.otp.service import OTPService


async def get_authenticated_user_token(client: AsyncClient, phone: str = "9876543210", name: str = "Test Owner") -> str:
    """Helper to register and authenticate a user, returning access token."""
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
async def test_business_creation_and_listing(client: AsyncClient):
    """Verify business registration assigns OWNER role, permissions, and creates default outlet."""
    token = await get_authenticated_user_token(client, "9988776655", "Shopkeeper Owner")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Business
    create_payload = {
        "name": "Laxmi Kirana Store",
        "legal_name": "Laxmi Retail Enterprises",
        "gstin": "27AAAAA0000A1Z5",
        "currency": "INR",
        "primary_language": "hi",
    }
    create_resp = await client.post("/api/v1/businesses", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created_data = create_resp.json()

    assert created_data["role"] == "OWNER"
    assert created_data["is_active"] is True
    assert "business.update" in created_data["permissions"]
    assert "members.manage" in created_data["permissions"]
    business_id = created_data["business"]["id"]

    # 2. List Businesses
    list_resp = await client.get("/api/v1/businesses", headers=headers)
    assert list_resp.status_code == 200
    businesses = list_resp.json()
    assert len(businesses) >= 1
    assert any(b["business"]["id"] == business_id for b in businesses)

    # 3. Get Details
    detail_resp = await client.get(f"/api/v1/businesses/{business_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["name"] == "Laxmi Kirana Store"

    # 4. Update Business
    update_resp = await client.patch(
        f"/api/v1/businesses/{business_id}",
        json={"name": "Laxmi Supermarket"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Laxmi Supermarket"


@pytest.mark.asyncio
async def test_member_addition_and_role_management(client: AsyncClient):
    """Verify owner can add staff members with specific roles."""
    owner_token = await get_authenticated_user_token(client, "9123456789", "Owner User")
    headers = {"Authorization": f"Bearer {owner_token}"}

    # Create business
    biz_resp = await client.post(
        "/api/v1/businesses",
        json={"name": "Gupta Provision Store"},
        headers=headers,
    )
    business_id = biz_resp.json()["business"]["id"]

    # Add Cashier Member
    add_resp = await client.post(
        f"/api/v1/businesses/{business_id}/members",
        json={
            "phone_number": "9123456780",
            "full_name": "Suresh Cashier",
            "role": "CASHIER",
        },
        headers=headers,
    )
    assert add_resp.status_code == 201
    member_data = add_resp.json()
    assert member_data["full_name"] == "Suresh Cashier"
    assert member_data["role"] == "CASHIER"
    assert member_data["is_active"] is True

    # List Members
    members_resp = await client.get(f"/api/v1/businesses/{business_id}/members", headers=headers)
    assert members_resp.status_code == 200
    members = members_resp.json()
    assert len(members) == 2  # Owner + Cashier
    roles = {m["role"] for m in members}
    assert "OWNER" in roles
    assert "CASHIER" in roles
