"""
Integration Tests for DukaanAI Inventory Management & Stock Ledger API.
Validates:
- Opening stock recording and duplicate rejection
- Stock adjustments (Manual In, Manual Out, Damage, Expiry)
- Moving Weighted Average Cost (WAC) calculations
- Negative stock policy enforcement (DISALLOW vs ALLOW)
- Physical stock counting audit session lifecycle (create, count, complete, variance movements)
- Stock balance projection and summary KPIs
- Stock movement immutable ledger auditing
- Ledger reconciliation and projection repair
- Tenant isolation and RBAC permission checks
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
    Business,
    BusinessUser,
    Category,
    Product,
    ProductBarcode,
    ProductVariant,
    RefreshSession,
    StockBalance,
    StockMovement,
    Store,
    UnitOfMeasure,
    User,
)


@pytest.fixture
def inventory_test_setup(db_session: Session):
    """Sets up businesses, stores, users, products, and variants for inventory tests."""
    # UOM
    pcs = db_session.scalar(select(UnitOfMeasure).where(UnitOfMeasure.code == "PCS"))
    if not pcs:
        pcs = UnitOfMeasure(
            id=uuid.uuid4(),
            code="PCS",
            name="Piece",
            category="COUNT",
            is_fractional_allowed=False,
        )
        db_session.add(pcs)
        db_session.flush()

    # Business 1 (Owner + Cashier + Store)
    user_owner = User(
        phone_number="+919876540001",
        full_name="Rajesh Owner",
        password_hash=hash_password("password"),
        is_active=True,
    )
    user_cashier = User(
        phone_number="+919876540002",
        full_name="Vijay Cashier",
        password_hash=hash_password("password"),
        is_active=True,
    )
    user_other = User(
        phone_number="+919876540003",
        full_name="Sunil Other",
        password_hash=hash_password("password"),
        is_active=True,
    )
    db_session.add_all([user_owner, user_cashier, user_other])
    db_session.flush()

    biz1 = Business(
        name="Rajesh Grocery",
        legal_name="Rajesh Grocery Pvt Ltd",
        currency="INR",
        negative_stock_policy="DISALLOW_NEGATIVE_STOCK",
        is_active=True,
    )
    biz2 = Business(
        name="Other Store",
        legal_name="Other Store Ltd",
        currency="INR",
        negative_stock_policy="DISALLOW_NEGATIVE_STOCK",
        is_active=True,
    )
    db_session.add_all([biz1, biz2])
    db_session.flush()

    store1 = Store(
        business_id=biz1.id,
        name="Main Bazaar Store",
        code="MB01",
        address_line1="123 Main Bazaar",
        city="Mumbai",
        state="Maharashtra",
        pincode="400001",
        is_active=True,
    )
    store2 = Store(
        business_id=biz2.id,
        name="Cross Town Store",
        code="CT01",
        address_line1="456 Cross Town",
        city="Pune",
        state="Maharashtra",
        pincode="411001",
        is_active=True,
    )
    db_session.add_all([store1, store2])
    db_session.flush()

    bu_owner = BusinessUser(business_id=biz1.id, user_id=user_owner.id, role="OWNER", is_active=True)
    bu_cashier = BusinessUser(business_id=biz1.id, user_id=user_cashier.id, role="CASHIER", is_active=True)
    bu_other = BusinessUser(business_id=biz2.id, user_id=user_other.id, role="OWNER", is_active=True)
    db_session.add_all([bu_owner, bu_cashier, bu_other])

    # Refresh tokens
    expiry = datetime.now(timezone.utc) + timedelta(days=7)
    sess_owner = RefreshSession(user_id=user_owner.id, token_hash="inv_hash1", expires_at=expiry)
    sess_cashier = RefreshSession(user_id=user_cashier.id, token_hash="inv_hash2", expires_at=expiry)
    sess_other = RefreshSession(user_id=user_other.id, token_hash="inv_hash3", expires_at=expiry)
    db_session.add_all([sess_owner, sess_cashier, sess_other])
    db_session.flush()

    token_owner = create_access_token(user_owner.id, sess_owner.id)
    token_cashier = create_access_token(user_cashier.id, sess_cashier.id)
    token_other = create_access_token(user_other.id, sess_other.id)

    # Category
    category = Category(
        business_id=biz1.id,
        name="Biscuits",
        is_active=True,
    )
    db_session.add(category)
    db_session.flush()

    # Product & Variants
    product = Product(
        business_id=biz1.id,
        category_id=category.id,
        name="Parle-G",
        sku="PARLE-G-BASE",
        base_uom_id=pcs.id,
        selling_price=Decimal("10.0000"),
        mrp=Decimal("10.0000"),
        is_active=True,
    )
    db_session.add(product)
    db_session.flush()

    variant1 = ProductVariant(
        business_id=biz1.id,
        product_id=product.id,
        variant_name="Parle-G 100g",
        sku="PARLE-G-100G",
        base_uom_id=pcs.id,
        cost_price=Decimal("10.0000"),
        selling_price=Decimal("12.0000"),
        mrp=Decimal("12.0000"),
        is_active=True,
    )
    variant2 = ProductVariant(
        business_id=biz1.id,
        product_id=product.id,
        variant_name="Parle-G 200g",
        sku="PARLE-G-200G",
        base_uom_id=pcs.id,
        cost_price=Decimal("20.0000"),
        selling_price=Decimal("25.0000"),
        mrp=Decimal("25.0000"),
        is_active=True,
    )
    db_session.add_all([variant1, variant2])
    db_session.flush()

    bc1 = ProductBarcode(
        business_id=biz1.id,
        product_id=product.id,
        variant_id=variant1.id,
        barcode="890103000001",
        is_primary=True,
    )
    bc2 = ProductBarcode(
        business_id=biz1.id,
        product_id=product.id,
        variant_id=variant2.id,
        barcode="890103000002",
        is_primary=True,
    )
    db_session.add_all([bc1, bc2])
    db_session.commit()

    return {
        "biz1": biz1,
        "biz2": biz2,
        "store1": store1,
        "store2": store2,
        "variant1": variant1,
        "variant2": variant2,
        "token_owner": token_owner,
        "token_cashier": token_cashier,
        "token_other": token_other,
    }


@pytest.mark.asyncio
async def test_opening_stock_and_duplicate_prevention(client: AsyncClient, inventory_test_setup: dict):
    b_id = str(inventory_test_setup["biz1"].id)
    s_id = str(inventory_test_setup["store1"].id)
    v_id = str(inventory_test_setup["variant1"].id)
    headers = {"Authorization": f"Bearer {inventory_test_setup['token_owner']}"}

    # 1. Record Opening Stock
    payload = {
        "variant_id": v_id,
        "quantity": "50.0000",
        "unit_cost": "10.0000",
        "notes": "Initial store setup",
    }
    resp = await client.post(
        f"/api/v1/businesses/{b_id}/stores/{s_id}/inventory/opening-stock",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert Decimal(str(data["current_quantity"])) == Decimal("50.0000")
    assert Decimal(str(data["moving_average_cost"])) == Decimal("10.0000")

    # 2. Duplicate Opening Stock should be rejected with 409
    resp_dup = await client.post(
        f"/api/v1/businesses/{b_id}/stores/{s_id}/inventory/opening-stock",
        json=payload,
        headers=headers,
    )
    assert resp_dup.status_code == 409


@pytest.mark.asyncio
async def test_moving_weighted_average_cost_and_adjustments(client: AsyncClient, inventory_test_setup: dict):
    b_id = str(inventory_test_setup["biz1"].id)
    s_id = str(inventory_test_setup["store1"].id)
    v_id = str(inventory_test_setup["variant2"].id)
    headers = {"Authorization": f"Bearer {inventory_test_setup['token_owner']}"}

    # 1. Opening stock: 50 units @ 10.00
    await client.post(
        f"/api/v1/businesses/{b_id}/stores/{s_id}/inventory/opening-stock",
        json={"variant_id": v_id, "quantity": "50.0000", "unit_cost": "10.0000"},
        headers=headers,
    )

    # 2. Inward Adjustment: +20 units @ 16.00
    # Expected WAC: ((50 * 10) + (20 * 16)) / (50 + 20) = 820 / 70 = 11.7143
    resp_in = await client.post(
        f"/api/v1/businesses/{b_id}/stores/{s_id}/inventory/adjustments",
        json={
            "variant_id": v_id,
            "adjustment_type": "MANUAL_IN",
            "quantity": "20.0000",
            "unit_cost": "16.0000",
            "reason": "Supplier bonus stock",
        },
        headers=headers,
    )
    assert resp_in.status_code == 201
    data_in = resp_in.json()
    assert Decimal(str(data_in["new_quantity"])) == Decimal("70.0000")
    assert Decimal(str(data_in["moving_average_cost"])) == Decimal("11.7143")

    # 3. Outward Adjustment: -10 units (Damage)
    # WAC should remain unchanged at 11.7143
    resp_out = await client.post(
        f"/api/v1/businesses/{b_id}/stores/{s_id}/inventory/adjustments",
        json={
            "variant_id": v_id,
            "adjustment_type": "DAMAGE",
            "quantity": "10.0000",
            "reason": "Water leakage in warehouse",
        },
        headers=headers,
    )
    assert resp_out.status_code == 201
    data_out = resp_out.json()
    assert Decimal(str(data_out["new_quantity"])) == Decimal("60.0000")
    assert Decimal(str(data_out["moving_average_cost"])) == Decimal("11.7143")


@pytest.mark.asyncio
async def test_negative_stock_policy_enforcement(client: AsyncClient, inventory_test_setup: dict, db_session: Session):
    b_id = str(inventory_test_setup["biz1"].id)
    s_id = str(inventory_test_setup["store1"].id)
    v_id = str(inventory_test_setup["variant1"].id)
    headers = {"Authorization": f"Bearer {inventory_test_setup['token_owner']}"}

    # 1. Attempt outward deduction when current stock is 0 (or lower than quantity)
    # Default policy is DISALLOW_NEGATIVE_STOCK -> should fail with 422
    resp_fail = await client.post(
        f"/api/v1/businesses/{b_id}/stores/{s_id}/inventory/adjustments",
        json={
            "variant_id": v_id,
            "adjustment_type": "MANUAL_OUT",
            "quantity": "100.0000",
            "reason": "Test excessive deduction",
        },
        headers=headers,
    )
    assert resp_fail.status_code == 422
    assert "Insufficient stock" in resp_fail.json()["error"]["message"]

    # 2. Change business policy to ALLOW_NEGATIVE_STOCK
    biz = db_session.get(Business, inventory_test_setup["biz1"].id)
    biz.negative_stock_policy = "ALLOW_NEGATIVE_STOCK"
    db_session.commit()

    # 3. Retry outward deduction -> should succeed and drop into negative stock
    resp_success = await client.post(
        f"/api/v1/businesses/{b_id}/stores/{s_id}/inventory/adjustments",
        json={
            "variant_id": v_id,
            "adjustment_type": "MANUAL_OUT",
            "quantity": "10.0000",
            "reason": "Allowed negative deduction",
        },
        headers=headers,
    )
    assert resp_success.status_code == 201
    assert Decimal(str(resp_success.json()["new_quantity"])) == Decimal("-10.0000")


@pytest.mark.asyncio
async def test_physical_stock_count_workflow(client: AsyncClient, inventory_test_setup: dict):
    b_id = str(inventory_test_setup["biz1"].id)
    s_id = str(inventory_test_setup["store1"].id)
    v_id = str(inventory_test_setup["variant1"].id)
    headers = {"Authorization": f"Bearer {inventory_test_setup['token_owner']}"}

    # 1. Create Count Session
    resp_sess = await client.post(
        f"/api/v1/businesses/{b_id}/stores/{s_id}/inventory/counts",
        json={"notes": "Monthly physical audit"},
        headers=headers,
    )
    assert resp_sess.status_code == 201
    session_id = resp_sess.json()["id"]
    assert resp_sess.json()["status"] == "OPEN"

    # 2. Record Count Item (e.g. physical count is 45 units)
    resp_item = await client.post(
        f"/api/v1/businesses/{b_id}/stores/{s_id}/inventory/counts/{session_id}/items",
        json={"variant_id": v_id, "counted_quantity": "45.0000", "notes": "Found in aisle 2"},
        headers=headers,
    )
    assert resp_item.status_code == 201
    assert Decimal(str(resp_item.json()["counted_quantity"])) == Decimal("45.0000")

    # 3. Retrieve Session Details
    resp_get = await client.get(
        f"/api/v1/businesses/{b_id}/stores/{s_id}/inventory/counts/{session_id}",
        headers=headers,
    )
    assert resp_get.status_code == 200
    assert len(resp_get.json()["items"]) == 1

    # 4. Complete Session
    resp_comp = await client.post(
        f"/api/v1/businesses/{b_id}/stores/{s_id}/inventory/counts/{session_id}/complete",
        headers=headers,
    )
    assert resp_comp.status_code == 200
    assert resp_comp.json()["status"] == "COMPLETED"

    # 5. Verify stock balance was updated to 45.0000
    resp_detail = await client.get(
        f"/api/v1/businesses/{b_id}/stores/{s_id}/inventory/{v_id}",
        headers=headers,
    )
    assert resp_detail.status_code == 200
    assert Decimal(str(resp_detail.json()["current_quantity"])) == Decimal("45.0000")


@pytest.mark.asyncio
async def test_inventory_summary_and_ledger_reconciliation(client: AsyncClient, inventory_test_setup: dict, db_session: Session):
    b_id = str(inventory_test_setup["biz1"].id)
    s_id = str(inventory_test_setup["store1"].id)
    v_id = str(inventory_test_setup["variant1"].id)
    headers = {"Authorization": f"Bearer {inventory_test_setup['token_owner']}"}

    # 1. Summary
    resp_sum = await client.get(
        f"/api/v1/businesses/{b_id}/stores/{s_id}/inventory",
        headers=headers,
    )
    assert resp_sum.status_code == 200
    sum_data = resp_sum.json()
    assert sum_data["total_items"] >= 2
    assert "total_valuation" in sum_data

    # 2. Movement Ledger
    resp_mov = await client.get(
        f"/api/v1/businesses/{b_id}/stores/{s_id}/inventory/{v_id}/movements",
        headers=headers,
    )
    assert resp_mov.status_code == 200
    assert "items" in resp_mov.json()

    # 3. Desynchronize balance to simulate projection corruption
    bal = db_session.execute(
        select(StockBalance).where(
            StockBalance.business_id == inventory_test_setup["biz1"].id,
            StockBalance.store_id == inventory_test_setup["store1"].id,
            StockBalance.variant_id == inventory_test_setup["variant1"].id,
        )
    ).scalar_one_or_none()

    if bal:
        bal.current_quantity = Decimal("999.0000")
        db_session.commit()

        # Run Reconciliation & Repair
        resp_recon = await client.post(
            f"/api/v1/businesses/{b_id}/stores/{s_id}/inventory/reconciliation",
            headers=headers,
        )
        assert resp_recon.status_code == 200
        recon_data = resp_recon.json()
        assert recon_data["discrepancies_repaired"] >= 1

        # Check repaired balance
        db_session.expire_all()
        bal_repaired = db_session.get(StockBalance, bal.id)
        assert bal_repaired.current_quantity != Decimal("999.0000")


@pytest.mark.asyncio
async def test_rbac_and_tenant_isolation(client: AsyncClient, inventory_test_setup: dict):
    b_id1 = str(inventory_test_setup["biz1"].id)
    b_id2 = str(inventory_test_setup["biz2"].id)
    s_id1 = str(inventory_test_setup["store1"].id)
    v_id1 = str(inventory_test_setup["variant1"].id)

    # 1. Cashier lacks INVENTORY_ADJUST permission -> 403 Forbidden
    resp_cashier = await client.post(
        f"/api/v1/businesses/{b_id1}/stores/{s_id1}/inventory/adjustments",
        json={"variant_id": v_id1, "adjustment_type": "DAMAGE", "quantity": "1.0000", "reason": "Test"},
        headers={"Authorization": f"Bearer {inventory_test_setup['token_cashier']}"},
    )
    assert resp_cashier.status_code == 403

    # 2. Cross-tenant access: User from Biz 2 cannot access Biz 1's inventory -> 403
    resp_cross = await client.get(
        f"/api/v1/businesses/{b_id1}/stores/{s_id1}/inventory",
        headers={"Authorization": f"Bearer {inventory_test_setup['token_other']}"},
    )
    assert resp_cross.status_code == 403
