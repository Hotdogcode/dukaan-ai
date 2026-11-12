"""
Integration Tests for DukaanAI Product Catalogue API.
Validates product creation, multi-variant handling, barcode indexing, category hierarchies,
decimal pricing rules, SKU/barcode uniqueness, tenant isolation, and RBAC permissions.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, hash_password
from backend.app.infrastructure.database.models import (
    Brand,
    Business,
    BusinessUser,
    Category,
    Product,
    ProductBarcode,
    ProductVariant,
    RefreshSession,
    StandardUnitConversion,
    UnitOfMeasure,
    User,
)


@pytest.fixture
def uom_fixture(db_session: Session) -> dict[str, UnitOfMeasure]:
    """Populates standard retail units of measure for test runs."""
    units_data = [
        ("KG", "Kilogram", "MASS", True),
        ("GM", "Gram", "MASS", True),
        ("L", "Litre", "VOLUME", True),
        ("ML", "Millilitre", "VOLUME", True),
        ("PCS", "Piece", "COUNT", False),
        ("DOZ", "Dozen", "COUNT", True),
    ]
    uoms = {}
    for code, name, category, is_fractional in units_data:
        existing = db_session.scalar(select(UnitOfMeasure).where(UnitOfMeasure.code == code))
        if not existing:
            uom = UnitOfMeasure(
                id=uuid.uuid4(),
                code=code,
                name=name,
                category=category,
                is_fractional_allowed=is_fractional,
            )
            db_session.add(uom)
            db_session.flush()
            uoms[code] = uom
        else:
            uoms[code] = existing
    db_session.commit()
    return uoms


@pytest.fixture
def test_setup(db_session: Session, uom_fixture: dict[str, UnitOfMeasure]):
    """Creates test businesses, users, and tokens."""
    # User 1: Owner of Business 1
    user1 = User(phone_number="+919876500001", full_name="Ramesh Owner", password_hash=hash_password("test"), is_active=True)
    db_session.add(user1)
    db_session.flush()

    business1 = Business(name="Ramesh Kirana Store", legal_name="Ramesh Kirana Pvt Ltd", currency="INR", is_active=True)
    db_session.add(business1)
    db_session.flush()

    bu1 = BusinessUser(business_id=business1.id, user_id=user1.id, role="OWNER", is_active=True)
    db_session.add(bu1)

    expiry = datetime.now(timezone.utc) + timedelta(days=7)
    sess1 = RefreshSession(user_id=user1.id, token_hash="hash1", expires_at=expiry, revoked_at=None)
    db_session.add(sess1)
    db_session.flush()
    token1 = create_access_token(user1.id, sess1.id)

    # User 2: Cashier of Business 1
    user2 = User(phone_number="+919876500002", full_name="Suresh Cashier", password_hash=hash_password("test"), is_active=True)
    db_session.add(user2)
    db_session.flush()

    bu2 = BusinessUser(business_id=business1.id, user_id=user2.id, role="CASHIER", is_active=True)
    db_session.add(bu2)

    sess2 = RefreshSession(user_id=user2.id, token_hash="hash2", expires_at=expiry, revoked_at=None)
    db_session.add(sess2)
    db_session.flush()
    token2 = create_access_token(user2.id, sess2.id)

    # User 3: Owner of Business 2 (Tenant Isolation)
    user3 = User(phone_number="+919876500003", full_name="Other Owner", password_hash=hash_password("test"), is_active=True)
    db_session.add(user3)
    db_session.flush()

    business2 = Business(name="Gupta General Store", legal_name="Gupta General Pvt Ltd", currency="INR", is_active=True)
    db_session.add(business2)
    db_session.flush()

    bu3 = BusinessUser(business_id=business2.id, user_id=user3.id, role="OWNER", is_active=True)
    db_session.add(bu3)

    sess3 = RefreshSession(user_id=user3.id, token_hash="hash3", expires_at=expiry, revoked_at=None)
    db_session.add(sess3)
    db_session.flush()
    token3 = create_access_token(user3.id, sess3.id)

    db_session.commit()

    return {
        "user1": user1,
        "business1": business1,
        "token1": token1,
        "user2": user2,
        "token2": token2,
        "user3": user3,
        "business2": business2,
        "token3": token3,
        "uoms": uom_fixture,
    }


# -----------------------------------------------------------------------------
# Unit of Measure Tests
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_list_units(client: AsyncClient, test_setup: dict):
    resp = await client.get("/api/v1/units", headers={"Authorization": f"Bearer {test_setup['token1']}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 6
    codes = [u["code"] for u in data]
    assert "KG" in codes
    assert "PCS" in codes


# -----------------------------------------------------------------------------
# Brands & Categories Tests
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_brand_lifecycle(client: AsyncClient, test_setup: dict):
    b_id = str(test_setup["business1"].id)
    headers = {"Authorization": f"Bearer {test_setup['token1']}"}

    # 1. Create Brand
    resp = await client.post(f"/api/v1/businesses/{b_id}/brands", json={"name": "Tata", "description": "Tata Consumer"}, headers=headers)
    assert resp.status_code == 201
    brand_id = resp.json()["id"]
    assert resp.json()["name"] == "Tata"

    # 2. Duplicate Brand rejected
    resp_dup = await client.post(f"/api/v1/businesses/{b_id}/brands", json={"name": "TATA"}, headers=headers)
    assert resp_dup.status_code == 422

    # 3. List Brands
    resp_list = await client.get(f"/api/v1/businesses/{b_id}/brands", headers=headers)
    assert resp_list.status_code == 200
    assert any(b["id"] == brand_id for b in resp_list.json())

    # 4. Update Brand
    resp_up = await client.patch(f"/api/v1/businesses/{b_id}/brands/{brand_id}", json={"description": "Updated"}, headers=headers)
    assert resp_up.status_code == 200
    assert resp_up.json()["description"] == "Updated"


@pytest.mark.asyncio
async def test_category_hierarchy_and_cycle_prevention(client: AsyncClient, test_setup: dict):
    b_id = str(test_setup["business1"].id)
    headers = {"Authorization": f"Bearer {test_setup['token1']}"}

    # 1. Create Parent Category
    resp_p = await client.post(f"/api/v1/businesses/{b_id}/categories", json={"name": "Beverages"}, headers=headers)
    assert resp_p.status_code == 201
    parent_id = resp_p.json()["id"]

    # 2. Create Child Category
    resp_c = await client.post(f"/api/v1/businesses/{b_id}/categories", json={"name": "Tea", "parent_id": parent_id}, headers=headers)
    assert resp_c.status_code == 201
    child_id = resp_c.json()["id"]

    # 3. Prevent self-parenting
    resp_self = await client.patch(f"/api/v1/businesses/{b_id}/categories/{parent_id}", json={"parent_id": parent_id}, headers=headers)
    assert resp_self.status_code == 422

    # 4. Prevent circular hierarchy (setting parent's parent to child)
    resp_cycle = await client.patch(f"/api/v1/businesses/{b_id}/categories/{parent_id}", json={"parent_id": child_id}, headers=headers)
    assert resp_cycle.status_code == 422


# -----------------------------------------------------------------------------
# Product Creation & Pricing Rules
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_product_creation_and_price_invariants(client: AsyncClient, test_setup: dict):
    b_id = str(test_setup["business1"].id)
    headers = {"Authorization": f"Bearer {test_setup['token1']}"}
    pcs_id = str(test_setup["uoms"]["PCS"].id)

    # 1. Valid Product
    payload = {
        "name": "Tata Salt 1kg",
        "sku": "TATA-SALT-1KG",
        "base_uom_id": pcs_id,
        "cost_price": "22.50",
        "selling_price": "26.00",
        "mrp": "28.00",
        "tax_rate_percent": "5.00",
        "is_tax_inclusive": True,
        "barcodes": ["8901234567890"],
    }
    resp = await client.post(f"/api/v1/businesses/{b_id}/products", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Tata Salt 1kg"
    assert Decimal(str(data["selling_price"])) == Decimal("26.00")
    assert Decimal(str(data["mrp"])) == Decimal("28.00")
    assert len(data["barcodes"]) == 1
    assert data["barcodes"][0]["barcode"] == "8901234567890"

    # 2. Invariant: Selling price > MRP rejected
    invalid_mrp = {
        "name": "Invalid Salt",
        "sku": "INVALID-SALT-01",
        "base_uom_id": pcs_id,
        "selling_price": "35.00",
        "mrp": "30.00",
    }
    resp_inv = await client.post(f"/api/v1/businesses/{b_id}/products", json=invalid_mrp, headers=headers)
    assert resp_inv.status_code == 422

    # 3. Invariant: Negative price rejected
    invalid_neg = {
        "name": "Negative Salt",
        "sku": "INVALID-SALT-02",
        "base_uom_id": pcs_id,
        "selling_price": "-5.00",
        "mrp": "30.00",
    }
    resp_neg = await client.post(f"/api/v1/businesses/{b_id}/products", json=invalid_neg, headers=headers)
    assert resp_neg.status_code == 422

    # 4. Invariant: Duplicate SKU rejected
    resp_dup = await client.post(f"/api/v1/businesses/{b_id}/products", json=payload, headers=headers)
    assert resp_dup.status_code == 422


# -----------------------------------------------------------------------------
# Multi-Variant Products & Barcode Lookup
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_multi_variant_product_and_barcode_lookup(client: AsyncClient, test_setup: dict):
    b_id = str(test_setup["business1"].id)
    headers = {"Authorization": f"Bearer {test_setup['token1']}"}
    pcs_id = str(test_setup["uoms"]["PCS"].id)

    payload = {
        "name": "Parle-G Biscuits",
        "sku": "PARLE-G-BASE",
        "base_uom_id": pcs_id,
        "selling_price": "10.00",
        "mrp": "10.00",
        "variants": [
            {
                "variant_name": "Parle-G 50g",
                "sku": "PARLE-G-50G",
                "base_uom_id": pcs_id,
                "cost_price": "4.20",
                "selling_price": "5.00",
                "mrp": "5.00",
                "barcodes": ["8901719100011"],
            },
            {
                "variant_name": "Parle-G 100g",
                "sku": "PARLE-G-100G",
                "base_uom_id": pcs_id,
                "cost_price": "8.50",
                "selling_price": "10.00",
                "mrp": "10.00",
                "barcodes": ["8901719100028"],
            },
        ],
    }

    resp = await client.post(f"/api/v1/businesses/{b_id}/products", json=payload, headers=headers)
    assert resp.status_code == 201
    prod_data = resp.json()
    assert prod_data["has_variants"] is True
    assert len(prod_data["variants"]) == 2

    # Test Barcode Lookup for Variant 1 (8901719100011)
    bc_resp = await client.get(f"/api/v1/businesses/{b_id}/barcodes/8901719100011", headers=headers)
    assert bc_resp.status_code == 200
    bc_data = bc_resp.json()
    assert bc_data["barcode"] == "8901719100011"
    assert bc_data["product"]["name"] == "Parle-G Biscuits"
    assert bc_data["variant"]["variant_name"] == "Parle-G 50g"


# -----------------------------------------------------------------------------
# Search, Filtering, and Pagination
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_search_and_filtering(client: AsyncClient, test_setup: dict):
    b_id = str(test_setup["business1"].id)
    headers = {"Authorization": f"Bearer {test_setup['token1']}"}
    pcs_id = str(test_setup["uoms"]["PCS"].id)

    # Seed 2 products
    await client.post(
        f"/api/v1/businesses/{b_id}/products",
        json={"name": "Fortune Sunflower Oil", "sku": "FORT-OIL-1L", "base_uom_id": pcs_id, "selling_price": "150.00", "mrp": "165.00"},
        headers=headers,
    )
    await client.post(
        f"/api/v1/businesses/{b_id}/products",
        json={"name": "Aashirvaad Atta 5kg", "sku": "AASH-ATTA-5KG", "base_uom_id": pcs_id, "selling_price": "230.00", "mrp": "250.00"},
        headers=headers,
    )

    # 1. Search by name
    s1 = await client.get(f"/api/v1/businesses/{b_id}/products?search=sunflower", headers=headers)
    assert s1.status_code == 200
    assert len(s1.json()["items"]) == 1
    assert "Sunflower" in s1.json()["items"][0]["name"]

    # 2. Search by SKU
    s2 = await client.get(f"/api/v1/businesses/{b_id}/products?search=AASH-ATTA", headers=headers)
    assert s2.status_code == 200
    assert len(s2.json()["items"]) == 1

    # 3. Pagination
    p = await client.get(f"/api/v1/businesses/{b_id}/products?page=1&page_size=1", headers=headers)
    assert p.status_code == 200
    assert len(p.json()["items"]) == 1
    assert p.json()["total"] >= 2


# -----------------------------------------------------------------------------
# Tenant Isolation & Role Permissions
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_tenant_isolation_and_rbac(client: AsyncClient, test_setup: dict):
    b1_id = str(test_setup["business1"].id)
    b2_id = str(test_setup["business2"].id)
    owner1_headers = {"Authorization": f"Bearer {test_setup['token1']}"}
    cashier1_headers = {"Authorization": f"Bearer {test_setup['token2']}"}
    owner2_headers = {"Authorization": f"Bearer {test_setup['token3']}"}
    pcs_id = str(test_setup["uoms"]["PCS"].id)

    # 1. Owner 1 creates product in Business 1
    resp = await client.post(
        f"/api/v1/businesses/{b1_id}/products",
        json={"name": "Maggi Noodles", "sku": "MAGGI-70G", "base_uom_id": pcs_id, "selling_price": "14.00", "mrp": "14.00"},
        headers=owner1_headers,
    )
    assert resp.status_code == 201
    prod_id = resp.json()["id"]

    # 2. Owner 2 (Business 2) CANNOT access Business 1 products (403 Forbidden)
    resp_cross = await client.get(f"/api/v1/businesses/{b1_id}/products/{prod_id}", headers=owner2_headers)
    assert resp_cross.status_code == 403

    # 3. Cashier CAN read products in Business 1
    resp_cash_read = await client.get(f"/api/v1/businesses/{b1_id}/products/{prod_id}", headers=cashier1_headers)
    assert resp_cash_read.status_code == 200

    # 4. Cashier CANNOT create or update products (403 Insufficient Permissions)
    resp_cash_create = await client.post(
        f"/api/v1/businesses/{b1_id}/products",
        json={"name": "Unauthorized Item", "sku": "UNAUTH-01", "base_uom_id": pcs_id, "selling_price": "10.00", "mrp": "10.00"},
        headers=cashier1_headers,
    )
    assert resp_cash_create.status_code == 403
