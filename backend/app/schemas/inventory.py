"""
Pydantic Schemas for DukaanAI Inventory Management & Stock Ledger.
Enforces business invariants, non-negative quantities, decimal precision, and strict tenant typing.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StockMovementType(str, Enum):
    OPENING_STOCK = "OPENING_STOCK"
    PURCHASE_RECEIVED = "PURCHASE_RECEIVED"
    SALE = "SALE"
    SALE_RETURN = "SALE_RETURN"
    PURCHASE_RETURN = "PURCHASE_RETURN"
    MANUAL_ADJUSTMENT_IN = "MANUAL_ADJUSTMENT_IN"
    MANUAL_ADJUSTMENT_OUT = "MANUAL_ADJUSTMENT_OUT"
    DAMAGE = "DAMAGE"
    EXPIRY = "EXPIRY"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    REVERSAL = "REVERSAL"
    AUDIT_ADJUSTMENT = "AUDIT_ADJUSTMENT"


class StockAdjustmentType(str, Enum):
    MANUAL_IN = "MANUAL_IN"
    MANUAL_OUT = "MANUAL_OUT"
    DAMAGE = "DAMAGE"
    EXPIRY = "EXPIRY"
    COUNT_CORRECTION = "COUNT_CORRECTION"


class NegativeStockPolicy(str, Enum):
    DISALLOW_NEGATIVE_STOCK = "DISALLOW_NEGATIVE_STOCK"
    ALLOW_NEGATIVE_STOCK = "ALLOW_NEGATIVE_STOCK"


class StockStatus(str, Enum):
    OUT_OF_STOCK = "OUT_OF_STOCK"
    LOW_STOCK = "LOW_STOCK"
    IN_STOCK = "IN_STOCK"
    OVERSTOCKED = "OVERSTOCKED"


# -----------------------------------------------------------------------------
# Opening Stock Schemas
# -----------------------------------------------------------------------------
class OpeningStockRequest(BaseModel):
    variant_id: uuid.UUID
    quantity: Decimal = Field(..., gt=0, decimal_places=4, description="Initial stock quantity (must be positive)")
    unit_cost: Decimal = Field(..., ge=0, decimal_places=4, description="Unit landing cost basis")
    notes: str | None = Field(default=None, max_length=255)


class OpeningStockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movement_id: uuid.UUID
    variant_id: uuid.UUID
    store_id: uuid.UUID
    quantity: Decimal
    unit_cost: Decimal
    current_quantity: Decimal
    moving_average_cost: Decimal
    recorded_at: datetime


# -----------------------------------------------------------------------------
# Stock Adjustment Schemas
# -----------------------------------------------------------------------------
class StockAdjustmentRequest(BaseModel):
    variant_id: uuid.UUID
    adjustment_type: StockAdjustmentType
    quantity: Decimal = Field(..., gt=0, decimal_places=4, description="Adjustment quantity (always positive)")
    unit_cost: Decimal | None = Field(default=None, ge=0, decimal_places=4, description="Unit cost for inward additions")
    reason: str = Field(..., min_length=1, max_length=100)
    notes: str | None = Field(default=None, max_length=255)


class StockAdjustmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    adjustment_id: uuid.UUID
    movement_id: uuid.UUID
    variant_id: uuid.UUID
    adjustment_type: str
    quantity: Decimal
    previous_quantity: Decimal
    new_quantity: Decimal
    moving_average_cost: Decimal
    recorded_at: datetime


# -----------------------------------------------------------------------------
# Physical Stock Count Schemas
# -----------------------------------------------------------------------------
class InventoryCountSessionCreate(BaseModel):
    notes: str | None = Field(default=None, max_length=255)


class InventoryCountItemCreate(BaseModel):
    variant_id: uuid.UUID
    counted_quantity: Decimal = Field(..., ge=0, decimal_places=4, description="Physical counted quantity")
    notes: str | None = Field(default=None, max_length=255)


class InventoryCountItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID
    product_name: str | None = None
    variant_name: str | None = None
    sku: str | None = None
    barcode: str | None = None
    expected_quantity: Decimal
    counted_quantity: Decimal
    variance_quantity: Decimal
    unit_cost: Decimal
    variance_value: Decimal
    notes: str | None = None


class InventoryCountSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    store_id: uuid.UUID
    session_number: str
    status: str
    total_variants_counted: int
    total_variance_quantity: Decimal
    total_variance_value: Decimal
    notes: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    items: list[InventoryCountItemResponse] = []


class CompleteCountSessionResponse(BaseModel):
    session_id: uuid.UUID
    status: str
    items_adjusted: int
    total_variance_value: Decimal
    completed_at: datetime


# -----------------------------------------------------------------------------
# Stock Movement Schemas
# -----------------------------------------------------------------------------
class StockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    store_id: uuid.UUID
    variant_id: uuid.UUID
    movement_type: str
    quantity: Decimal
    unit_cost: Decimal
    total_cost: Decimal
    balance_after: Decimal
    reference_type: str | None = None
    reference_id: uuid.UUID | None = None
    reason: str | None = None
    notes: str | None = None
    created_at: datetime
    created_by_user_id: uuid.UUID | None = None


class PaginatedStockMovementsResponse(BaseModel):
    items: list[StockMovementResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# -----------------------------------------------------------------------------
# Inventory Summary & Details Schemas
# -----------------------------------------------------------------------------
class InventorySummaryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    variant_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    variant_name: str
    sku: str | None = None
    barcode: str | None = None
    category_name: str | None = None
    current_quantity: Decimal
    uom_name: str
    moving_average_cost: Decimal
    selling_price: Decimal
    inventory_valuation: Decimal
    min_stock_level: Decimal
    reorder_quantity: Decimal
    stock_status: str
    last_movement_at: datetime | None = None


class InventorySummaryResponse(BaseModel):
    total_items: int
    total_valuation: Decimal
    low_stock_count: int
    out_of_stock_count: int
    items: list[InventorySummaryItemResponse]
    page: int
    limit: int
    total_pages: int


class StockDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    variant_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    variant_name: str
    sku: str | None = None
    barcode: str | None = None
    category_name: str | None = None
    current_quantity: Decimal
    uom_name: str
    moving_average_cost: Decimal
    selling_price: Decimal
    mrp: Decimal
    inventory_valuation: Decimal
    min_stock_level: Decimal
    reorder_quantity: Decimal
    stock_status: str
    has_opening_stock: bool


# -----------------------------------------------------------------------------
# Reconciliation Schema
# -----------------------------------------------------------------------------
class ReconciliationReportResponse(BaseModel):
    store_id: uuid.UUID
    total_variants_checked: int
    variants_reconciled: int
    discrepancies_repaired: int
    discrepancy_details: list[dict]
    reconciled_at: datetime
