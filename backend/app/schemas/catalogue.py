"""
Pydantic Schemas for DukaanAI Product Catalogue.
Enforces business invariants, non-negative decimal pricing, MRP boundaries, and strict tenant typing.
"""

from datetime import datetime
from decimal import Decimal
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# -----------------------------------------------------------------------------
# Unit of Measure Schemas
# -----------------------------------------------------------------------------
class UnitOfMeasureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    category: str
    is_fractional_allowed: bool


class StandardUnitConversionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    from_uom_id: uuid.UUID
    to_uom_id: uuid.UUID
    multiplier: Decimal
    dimension: str
    from_uom_code: str | None = None
    to_uom_code: str | None = None


# -----------------------------------------------------------------------------
# Brand Schemas
# -----------------------------------------------------------------------------
class BrandCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=255)

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Brand name cannot be empty or whitespace.")
        return s


class BrandUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class BrandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# Category Schemas
# -----------------------------------------------------------------------------
class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=255)
    parent_id: uuid.UUID | None = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Category name cannot be empty or whitespace.")
        return s


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=255)
    parent_id: uuid.UUID | None = None
    is_active: bool | None = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    name: str
    description: str | None
    parent_id: uuid.UUID | None
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CategoryTreeResponse(CategoryResponse):
    subcategories: list["CategoryTreeResponse"] = []


# -----------------------------------------------------------------------------
# Product Barcode Schemas
# -----------------------------------------------------------------------------
class ProductBarcodeCreate(BaseModel):
    barcode: str = Field(..., min_length=1, max_length=60)
    barcode_type: str = Field(default="EAN_13", max_length=30)
    is_primary: bool = True
    variant_id: uuid.UUID | None = None

    @field_validator("barcode")
    @classmethod
    def clean_barcode(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Barcode cannot be empty or whitespace.")
        return s


class ProductBarcodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID | None
    barcode: str
    barcode_type: str
    is_primary: bool
    created_at: datetime


# -----------------------------------------------------------------------------
# Product Variant Schemas
# -----------------------------------------------------------------------------
class ProductVariantCreate(BaseModel):
    variant_name: str = Field(..., min_length=1, max_length=100)
    sku: str = Field(..., min_length=1, max_length=60)
    base_uom_id: uuid.UUID
    cost_price: Decimal = Field(default=Decimal("0.0000"), ge=0)
    selling_price: Decimal = Field(..., ge=0)
    mrp: Decimal = Field(..., ge=0)
    tax_rate_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    is_tax_inclusive: bool = True
    is_active: bool = True
    barcodes: list[str] = Field(default_factory=list)

    @field_validator("sku", "variant_name")
    @classmethod
    def clean_strings(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Field cannot be empty or whitespace.")
        return s

    @model_validator(mode="after")
    def validate_pricing(self) -> "ProductVariantCreate":
        if self.selling_price > self.mrp:
            raise ValueError(f"Selling price ({self.selling_price}) cannot exceed MRP ({self.mrp}).")
        return self


class ProductVariantUpdate(BaseModel):
    variant_name: str | None = Field(default=None, min_length=1, max_length=100)
    sku: str | None = Field(default=None, min_length=1, max_length=60)
    base_uom_id: uuid.UUID | None = None
    cost_price: Decimal | None = Field(default=None, ge=0)
    selling_price: Decimal | None = Field(default=None, ge=0)
    mrp: Decimal | None = Field(default=None, ge=0)
    tax_rate_percent: Decimal | None = Field(default=None, ge=0, le=100)
    is_tax_inclusive: bool | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_pricing(self) -> "ProductVariantUpdate":
        if self.selling_price is not None and self.mrp is not None:
            if self.selling_price > self.mrp:
                raise ValueError(f"Selling price ({self.selling_price}) cannot exceed MRP ({self.mrp}).")
        return self


class ProductVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    product_id: uuid.UUID
    variant_name: str
    sku: str
    base_uom_id: uuid.UUID
    cost_price: Decimal
    selling_price: Decimal
    mrp: Decimal
    tax_rate_percent: Decimal
    is_tax_inclusive: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    barcodes: list[ProductBarcodeResponse] = []
    base_uom: UnitOfMeasureResponse | None = None


# -----------------------------------------------------------------------------
# Product Schemas
# -----------------------------------------------------------------------------
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    sku: str = Field(..., min_length=1, max_length=60)
    category_id: uuid.UUID | None = None
    brand_id: uuid.UUID | None = None
    description: str | None = Field(default=None, max_length=1000)
    image_url: str | None = Field(default=None, max_length=500)
    hsn_code: str | None = Field(default=None, max_length=20)
    base_uom_id: uuid.UUID
    selling_price: Decimal = Field(..., ge=0)
    mrp: Decimal = Field(..., ge=0)
    cost_price: Decimal = Field(default=Decimal("0.0000"), ge=0)
    tax_rate_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    is_tax_inclusive: bool = True
    reorder_threshold: Decimal = Field(default=Decimal("0.0000"), ge=0)
    is_loose_item: bool = False
    barcodes: list[str] = Field(default_factory=list)
    variants: list[ProductVariantCreate] = Field(default_factory=list)

    @field_validator("name", "sku")
    @classmethod
    def clean_strings(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Field cannot be empty or whitespace.")
        return s

    @model_validator(mode="after")
    def validate_pricing(self) -> "ProductCreate":
        if self.selling_price > self.mrp:
            raise ValueError(f"Selling price ({self.selling_price}) cannot exceed MRP ({self.mrp}).")
        return self


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    sku: str | None = Field(default=None, min_length=1, max_length=60)
    category_id: uuid.UUID | None = None
    brand_id: uuid.UUID | None = None
    description: str | None = Field(default=None, max_length=1000)
    image_url: str | None = Field(default=None, max_length=500)
    hsn_code: str | None = Field(default=None, max_length=20)
    base_uom_id: uuid.UUID | None = None
    selling_price: Decimal | None = Field(default=None, ge=0)
    mrp: Decimal | None = Field(default=None, ge=0)
    cost_price: Decimal | None = Field(default=None, ge=0)
    tax_rate_percent: Decimal | None = Field(default=None, ge=0, le=100)
    is_tax_inclusive: bool | None = None
    reorder_threshold: Decimal | None = Field(default=None, ge=0)
    is_loose_item: bool | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_pricing(self) -> "ProductUpdate":
        if self.selling_price is not None and self.mrp is not None:
            if self.selling_price > self.mrp:
                raise ValueError(f"Selling price ({self.selling_price}) cannot exceed MRP ({self.mrp}).")
        return self


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    category_id: uuid.UUID | None
    brand_id: uuid.UUID | None
    name: str
    description: str | None
    image_url: str | None
    sku: str
    hsn_code: str | None
    base_uom_id: uuid.UUID
    selling_price: Decimal
    mrp: Decimal
    cost_price: Decimal
    tax_rate_percent: Decimal
    is_tax_inclusive: bool
    reorder_threshold: Decimal
    is_loose_item: bool
    has_variants: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category: CategoryResponse | None = None
    brand: BrandResponse | None = None
    base_uom: UnitOfMeasureResponse | None = None
    barcodes: list[ProductBarcodeResponse] = []
    variants: list[ProductVariantResponse] = []


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
    pages: int


class BarcodeLookupResponse(BaseModel):
    barcode: str
    barcode_type: str
    product: ProductResponse
    variant: ProductVariantResponse | None = None
