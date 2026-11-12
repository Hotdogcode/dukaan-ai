"""
Integration and security tests for Store Outlets API.
Verifies CRUD operations, single primary store constraint, and tenant isolation.
"""

import pytest
from httpx import AsyncClient

from backend.app.infrastructure.otp.dev_provider import DevOTPProvider
from backend.app.infrastructure.otp.service import OTPService


async def get_authenticated_user_token(
    client: AsyncClient, phone: str = "9876543210", name: str = "Test Owner"
) -> str:
    """Helper to register and authenticate a user, returning access token."""
    await client.post("/api/v1/auth/otp/request", json={"phone_number": phone})
    provider = OTPService.get_provider()
    assert isinstance(provider, DevOTPProvider)
    otp = provider.get_latest_otp(f"+91{phone}")

    resp = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone_number": phone, "otp": otp, "full_name": name},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_store_lifecycle_and_single_primary_enforcement(client: AsyncClient):
    """Verifies store creation, listing, updating, and single primary outlet switching."""
    token = await get_authenticated_user_token(client, "9876543211", "Ramesh Gupta")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a business (creates default primary store)
    biz_res = await client.post(
        "/api/v1/businesses",
        json={
            "name": "Gupta Kirana Store",
            "business_type": "GROCERY",
            "owner_name": "Ramesh Gupta",
            "initial_store_name": "Gupta Kirana Main Branch",
        },
        headers=headers,
    )
    assert biz_res.status_code == 201
    business_id = biz_res.json()["business"]["id"]

    # 2. List stores - should have the default primary store
    list_res = await client.get(f"/api/v1/businesses/{business_id}/stores", headers=headers)
    assert list_res.status_code == 200
    stores = list_res.json()
    assert len(stores) == 1
    default_store = stores[0]
    assert default_store["name"] == "Gupta Kirana Main Branch"
    assert default_store["is_primary"] is True

    # 3. Create a second store marked as is_primary = True
    create_res = await client.post(
        f"/api/v1/businesses/{business_id}/stores",
        json={
            "name": "Gupta Kirana Express Outlet",
            "code": "EXP01",
            "address_line1": "Shop 4, Station Road",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400050",
            "is_primary": True,
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    second_store = create_res.json()
    assert second_store["name"] == "Gupta Kirana Express Outlet"
    assert second_store["is_primary"] is True

    # 4. Re-list stores: second store is primary, default store is now NOT primary
    re_list = await client.get(f"/api/v1/businesses/{business_id}/stores", headers=headers)
    assert re_list.status_code == 200
    updated_stores = re_list.json()
    assert len(updated_stores) == 2

    primary_stores = [s for s in updated_stores if s["is_primary"]]
    assert len(primary_stores) == 1
    assert primary_stores[0]["id"] == second_store["id"]

    # 5. Get store details by ID
    get_res = await client.get(f"/api/v1/businesses/{business_id}/stores/{second_store['id']}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["code"] == "EXP01"

    # 6. Update store details
    patch_res = await client.patch(
        f"/api/v1/businesses/{business_id}/stores/{second_store['id']}",
        json={"name": "Gupta Kirana Super Express"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Gupta Kirana Super Express"


@pytest.mark.asyncio
async def test_store_tenant_isolation(client: AsyncClient):
    """Verifies that a user from business B cannot access or modify stores from business A."""
    token_a = await get_authenticated_user_token(client, "9876543220", "User A")
    token_b = await get_authenticated_user_token(client, "9876543221", "User B")

    # Business A
    biz_a_resp = await client.post(
        "/api/v1/businesses",
        json={"name": "Shop A"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    biz_a = biz_a_resp.json()["business"]["id"]

    stores_a_resp = await client.get(
        f"/api/v1/businesses/{biz_a}/stores",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    stores_a = stores_a_resp.json()
    store_a_id = stores_a[0]["id"]

    # User B attempts to access Store A
    forbidden_get = await client.get(
        f"/api/v1/businesses/{biz_a}/stores/{store_a_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert forbidden_get.status_code in (403, 404)

    # User B attempts to modify Store A
    forbidden_patch = await client.patch(
        f"/api/v1/businesses/{biz_a}/stores/{store_a_id}",
        json={"name": "Hacked Store Name"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert forbidden_patch.status_code in (403, 404)
