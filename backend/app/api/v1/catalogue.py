"""
FastAPI Routes for Product Catalogue, Variants, Categories, Brands, Barcodes, and Units.
Enforces business membership, granular role permissions, and tenant isolation.
"""

from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies.auth import (
    get_current_user,
    get_tenant_membership,
    require_permission,
)
from backend.app.application.catalogue.service import CatalogueService
from backend.app.core.security import Permissions
from backend.app.infrastructure.database.models import BusinessUser, User
from backend.app.infrastructure.database.session import get_db_session
from backend.app.schemas.catalogue import (
    BarcodeLookupResponse,
    BrandCreate,
    BrandResponse,
    BrandUpdate,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    ProductBarcodeCreate,
    ProductBarcodeResponse,
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantResponse,
    ProductVariantUpdate,
    StandardUnitConversionResponse,
    UnitOfMeasureResponse,
)

router = APIRouter(tags=["Product Catalogue"])


# -----------------------------------------------------------------------------
# Global Units of Measure & Conversions (Authenticated Users)
# -----------------------------------------------------------------------------
@router.get(
    "/units",
    response_model=list[UnitOfMeasureResponse],
    summary="List Units of Measure",
    description="Lists all supported global reference retail units (e.g. PCS, KG, GM, L, ML, DOZ).",
)
def list_units(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[UnitOfMeasureResponse]:
    return CatalogueService.list_units(db)


@router.get(
    "/units/conversions",
    response_model=list[StandardUnitConversionResponse],
    summary="List Standard Unit Conversions",
    description="Lists mathematical unit conversions between compatible dimensions.",
)
def list_unit_conversions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[StandardUnitConversionResponse]:
    return CatalogueService.list_standard_conversions(db)


# -----------------------------------------------------------------------------
# Brands
# -----------------------------------------------------------------------------
@router.post(
    "/businesses/{business_id}/brands",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Brand",
)
def create_brand(
    business_id: uuid.UUID,
    payload: BrandCreate,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.BRANDS_MANAGE))],
    db: Annotated[Session, Depends(get_db_session)],
) -> BrandResponse:
    return CatalogueService.create_brand(db, business_id, payload)


@router.get(
    "/businesses/{business_id}/brands",
    response_model=list[BrandResponse],
    summary="List Brands",
)
def list_brands(
    business_id: uuid.UUID,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.PRODUCTS_READ))],
    db: Annotated[Session, Depends(get_db_session)],
    active_only: bool = Query(default=True),
) -> list[BrandResponse]:
    return CatalogueService.list_brands(db, business_id, active_only)


@router.patch(
    "/businesses/{business_id}/brands/{brand_id}",
    response_model=BrandResponse,
    summary="Update Brand",
)
def update_brand(
    business_id: uuid.UUID,
    brand_id: uuid.UUID,
    payload: BrandUpdate,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.BRANDS_MANAGE))],
    db: Annotated[Session, Depends(get_db_session)],
) -> BrandResponse:
    return CatalogueService.update_brand(db, business_id, brand_id, payload)


# -----------------------------------------------------------------------------
# Categories
# -----------------------------------------------------------------------------
@router.post(
    "/businesses/{business_id}/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Category",
)
def create_category(
    business_id: uuid.UUID,
    payload: CategoryCreate,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.CATEGORIES_MANAGE))],
    db: Annotated[Session, Depends(get_db_session)],
) -> CategoryResponse:
    return CatalogueService.create_category(db, business_id, payload)


@router.get(
    "/businesses/{business_id}/categories",
    response_model=list[CategoryResponse],
    summary="List Categories",
)
def list_categories(
    business_id: uuid.UUID,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.PRODUCTS_READ))],
    db: Annotated[Session, Depends(get_db_session)],
    active_only: bool = Query(default=True),
) -> list[CategoryResponse]:
    return CatalogueService.list_categories(db, business_id, active_only)


@router.patch(
    "/businesses/{business_id}/categories/{category_id}",
    response_model=CategoryResponse,
    summary="Update Category",
)
def update_category(
    business_id: uuid.UUID,
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.CATEGORIES_MANAGE))],
    db: Annotated[Session, Depends(get_db_session)],
) -> CategoryResponse:
    return CatalogueService.update_category(db, business_id, category_id, payload)


@router.delete(
    "/businesses/{business_id}/categories/{category_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete / Deactivate Category",
)
def delete_category(
    business_id: uuid.UUID,
    category_id: uuid.UUID,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.CATEGORIES_MANAGE))],
    db: Annotated[Session, Depends(get_db_session)],
) -> dict[str, str]:
    return CatalogueService.delete_category(db, business_id, category_id)


# -----------------------------------------------------------------------------
# Products
# -----------------------------------------------------------------------------
@router.post(
    "/businesses/{business_id}/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Product",
)
def create_product(
    business_id: uuid.UUID,
    payload: ProductCreate,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.PRODUCTS_CREATE))],
    db: Annotated[Session, Depends(get_db_session)],
) -> ProductResponse:
    return CatalogueService.create_product(db, business_id, payload)


@router.get(
    "/businesses/{business_id}/products",
    response_model=ProductListResponse,
    summary="List Products with Search and Filters",
)
def list_products(
    business_id: uuid.UUID,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.PRODUCTS_READ))],
    db: Annotated[Session, Depends(get_db_session)],
    search: str | None = Query(default=None),
    category_id: uuid.UUID | None = Query(default=None),
    brand_id: uuid.UUID | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="created_at_desc"),
) -> ProductListResponse:
    return CatalogueService.list_products(
        db,
        business_id,
        search=search,
        category_id=category_id,
        brand_id=brand_id,
        is_active=is_active,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
    )


@router.get(
    "/businesses/{business_id}/products/{product_id}",
    response_model=ProductResponse,
    summary="Get Product Details",
)
def get_product(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.PRODUCTS_READ))],
    db: Annotated[Session, Depends(get_db_session)],
) -> ProductResponse:
    return CatalogueService.get_product(db, business_id, product_id)


@router.patch(
    "/businesses/{business_id}/products/{product_id}",
    response_model=ProductResponse,
    summary="Update Product",
)
def update_product(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    payload: ProductUpdate,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.PRODUCTS_UPDATE))],
    db: Annotated[Session, Depends(get_db_session)],
) -> ProductResponse:
    return CatalogueService.update_product(db, business_id, product_id, payload)


@router.delete(
    "/businesses/{business_id}/products/{product_id}",
    status_code=status.HTTP_200_OK,
    summary="Deactivate Product",
)
def deactivate_product(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.PRODUCTS_DEACTIVATE))],
    db: Annotated[Session, Depends(get_db_session)],
) -> dict[str, str]:
    return CatalogueService.deactivate_product(db, business_id, product_id)


# -----------------------------------------------------------------------------
# Product Variants
# -----------------------------------------------------------------------------
@router.post(
    "/businesses/{business_id}/products/{product_id}/variants",
    response_model=ProductVariantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Product Variant",
)
def create_variant(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    payload: ProductVariantCreate,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.PRODUCTS_CREATE))],
    db: Annotated[Session, Depends(get_db_session)],
) -> ProductVariantResponse:
    return CatalogueService.create_variant(db, business_id, product_id, payload)


@router.get(
    "/businesses/{business_id}/products/{product_id}/variants",
    response_model=list[ProductVariantResponse],
    summary="List Product Variants",
)
def list_variants(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.PRODUCTS_READ))],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[ProductVariantResponse]:
    return CatalogueService.list_variants(db, business_id, product_id)


@router.patch(
    "/businesses/{business_id}/products/{product_id}/variants/{variant_id}",
    response_model=ProductVariantResponse,
    summary="Update Product Variant",
)
def update_variant(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    payload: ProductVariantUpdate,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.PRODUCTS_UPDATE))],
    db: Annotated[Session, Depends(get_db_session)],
) -> ProductVariantResponse:
    return CatalogueService.update_variant(db, business_id, product_id, variant_id, payload)


@router.delete(
    "/businesses/{business_id}/products/{product_id}/variants/{variant_id}",
    status_code=status.HTTP_200_OK,
    summary="Deactivate Product Variant",
)
def deactivate_variant(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.PRODUCTS_DEACTIVATE))],
    db: Annotated[Session, Depends(get_db_session)],
) -> dict[str, str]:
    return CatalogueService.deactivate_variant(db, business_id, product_id, variant_id)


# -----------------------------------------------------------------------------
# Barcodes
# -----------------------------------------------------------------------------
@router.post(
    "/businesses/{business_id}/products/{product_id}/barcodes",
    response_model=ProductBarcodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Product Barcode",
)
def add_product_barcode(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    payload: ProductBarcodeCreate,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.PRODUCTS_UPDATE))],
    db: Annotated[Session, Depends(get_db_session)],
) -> ProductBarcodeResponse:
    return CatalogueService.add_barcode(db, business_id, product_id, payload)


@router.post(
    "/businesses/{business_id}/products/{product_id}/variants/{variant_id}/barcodes",
    response_model=ProductBarcodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Variant Barcode",
)
def add_variant_barcode(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    payload: ProductBarcodeCreate,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.PRODUCTS_UPDATE))],
    db: Annotated[Session, Depends(get_db_session)],
) -> ProductBarcodeResponse:
    payload.variant_id = variant_id
    return CatalogueService.add_barcode(db, business_id, product_id, payload)


@router.get(
    "/businesses/{business_id}/barcodes/{barcode_value}",
    response_model=BarcodeLookupResponse,
    summary="Lookup Product and Variant by Barcode",
)
def lookup_barcode(
    business_id: uuid.UUID,
    barcode_value: str,
    membership: Annotated[BusinessUser, Depends(require_permission(Permissions.PRODUCTS_READ))],
    db: Annotated[Session, Depends(get_db_session)],
) -> BarcodeLookupResponse:
    return CatalogueService.lookup_barcode(db, business_id, barcode_value)
