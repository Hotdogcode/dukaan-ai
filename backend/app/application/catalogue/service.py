"""
Product Catalogue Application Service for DukaanAI.
Coordinates product creation, variant management, hierarchical category validation,
brand administration, fast barcode lookups, and multi-criteria catalogue search.
Enforces tenant isolation, decimal business rules, and safe archival.
"""

from decimal import Decimal
import math
import uuid
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from backend.app.core.exceptions import (
    BusinessRuleViolation,
    EntityNotFound,
    ValidationFailure,
)
from backend.app.infrastructure.database.models import (
    Brand,
    Category,
    Product,
    ProductBarcode,
    ProductVariant,
    StandardUnitConversion,
    UnitConversion,
    UnitOfMeasure,
)
from backend.app.schemas.catalogue import (
    BarcodeLookupResponse,
    BrandCreate,
    BrandResponse,
    BrandUpdate,
    CategoryCreate,
    CategoryResponse,
    CategoryTreeResponse,
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


class CatalogueService:
    """Core domain orchestrator for merchant product catalogues."""

    # -------------------------------------------------------------------------
    # Units of Measure
    # -------------------------------------------------------------------------
    @staticmethod
    def list_units(db: Session) -> list[UnitOfMeasureResponse]:
        """Lists all supported global reference units of measure."""
        stmt = select(UnitOfMeasure).order_by(UnitOfMeasure.category, UnitOfMeasure.code)
        units = db.scalars(stmt).all()
        return [UnitOfMeasureResponse.model_validate(u) for u in units]

    @staticmethod
    def list_standard_conversions(db: Session) -> list[StandardUnitConversionResponse]:
        """Lists standard dimensional conversions (e.g. 1 KG = 1000 GM)."""
        stmt = (
            select(StandardUnitConversion)
            .options(
                joinedload(StandardUnitConversion.from_uom),
                joinedload(StandardUnitConversion.to_uom),
            )
            .order_by(StandardUnitConversion.dimension)
        )
        conversions = db.scalars(stmt).all()
        results = []
        for c in conversions:
            results.append(
                StandardUnitConversionResponse(
                    id=c.id,
                    from_uom_id=c.from_uom_id,
                    to_uom_id=c.to_uom_id,
                    multiplier=c.multiplier,
                    dimension=c.dimension,
                    from_uom_code=c.from_uom.code if c.from_uom else None,
                    to_uom_code=c.to_uom.code if c.to_uom else None,
                )
            )
        return results

    # -------------------------------------------------------------------------
    # Brands
    # -------------------------------------------------------------------------
    @staticmethod
    def create_brand(db: Session, business_id: uuid.UUID, payload: BrandCreate) -> BrandResponse:
        """Creates a new merchant brand, verifying tenant uniqueness."""
        stmt = select(Brand).where(
            Brand.business_id == business_id,
            func.lower(Brand.name) == func.lower(payload.name),
        )
        existing = db.scalar(stmt)
        if existing:
            raise BusinessRuleViolation(f"Brand '{payload.name}' already exists in your catalogue.")

        brand = Brand(
            business_id=business_id,
            name=payload.name,
            description=payload.description,
            is_active=True,
        )
        db.add(brand)
        db.commit()
        db.refresh(brand)
        return BrandResponse.model_validate(brand)

    @staticmethod
    def list_brands(db: Session, business_id: uuid.UUID, active_only: bool = True) -> list[BrandResponse]:
        """Lists all brands for a business."""
        stmt = select(Brand).where(Brand.business_id == business_id)
        if active_only:
            stmt = stmt.where(Brand.is_active.is_(True))
        stmt = stmt.order_by(Brand.name.asc())
        brands = db.scalars(stmt).all()
        return [BrandResponse.model_validate(b) for b in brands]

    @staticmethod
    def update_brand(db: Session, business_id: uuid.UUID, brand_id: uuid.UUID, payload: BrandUpdate) -> BrandResponse:
        """Updates an existing brand."""
        brand = db.scalar(select(Brand).where(Brand.id == brand_id, Brand.business_id == business_id))
        if not brand:
            raise EntityNotFound("Brand not found in your catalogue.")

        if payload.name is not None and payload.name.lower() != brand.name.lower():
            stmt = select(Brand).where(
                Brand.business_id == business_id,
                func.lower(Brand.name) == func.lower(payload.name),
                Brand.id != brand_id,
            )
            if db.scalar(stmt):
                raise BusinessRuleViolation(f"Brand '{payload.name}' already exists in your catalogue.")
            brand.name = payload.name

        if payload.description is not None:
            brand.description = payload.description
        if payload.is_active is not None:
            brand.is_active = payload.is_active

        db.commit()
        db.refresh(brand)
        return BrandResponse.model_validate(brand)

    # -------------------------------------------------------------------------
    # Categories & Hierarchy
    # -------------------------------------------------------------------------
    @staticmethod
    def create_category(db: Session, business_id: uuid.UUID, payload: CategoryCreate) -> CategoryResponse:
        """Creates a category enforcing tenant uniqueness and valid parent hierarchy."""
        stmt = select(Category).where(
            Category.business_id == business_id,
            func.lower(Category.name) == func.lower(payload.name),
        )
        if db.scalar(stmt):
            raise BusinessRuleViolation(f"Category '{payload.name}' already exists in your catalogue.")

        if payload.parent_id:
            parent = db.scalar(select(Category).where(
                Category.id == payload.parent_id,
                or_(Category.business_id == business_id, Category.is_system.is_(True)),
            ))
            if not parent:
                raise ValidationFailure("Parent category not found.")

        category = Category(
            business_id=business_id,
            name=payload.name,
            description=payload.description,
            parent_id=payload.parent_id,
            is_system=False,
            is_active=True,
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return CategoryResponse.model_validate(category)

    @staticmethod
    def list_categories(db: Session, business_id: uuid.UUID, active_only: bool = True) -> list[CategoryResponse]:
        """Lists categories accessible to the merchant (custom business + system default)."""
        stmt = select(Category).where(
            or_(Category.business_id == business_id, Category.is_system.is_(True))
        )
        if active_only:
            stmt = stmt.where(Category.is_active.is_(True))
        stmt = stmt.order_by(Category.is_system.desc(), Category.name.asc())
        categories = db.scalars(stmt).all()
        return [CategoryResponse.model_validate(c) for c in categories]

    @staticmethod
    def update_category(db: Session, business_id: uuid.UUID, category_id: uuid.UUID, payload: CategoryUpdate) -> CategoryResponse:
        """Updates a category and prevents circular parent relationships."""
        category = db.scalar(select(Category).where(Category.id == category_id, Category.business_id == business_id))
        if not category:
            raise EntityNotFound("Category not found in your business catalogue.")

        if payload.name is not None and payload.name.lower() != category.name.lower():
            stmt = select(Category).where(
                Category.business_id == business_id,
                func.lower(Category.name) == func.lower(payload.name),
                Category.id != category_id,
            )
            if db.scalar(stmt):
                raise BusinessRuleViolation(f"Category '{payload.name}' already exists.")
            category.name = payload.name

        if payload.description is not None:
            category.description = payload.description

        if payload.parent_id is not None:
            if payload.parent_id == category_id:
                raise ValidationFailure("A category cannot be its own parent.")

            # Traverse parent chain to prevent cyclic dependencies
            curr = payload.parent_id
            visited = {category_id}
            while curr:
                if curr in visited:
                    raise ValidationFailure("Circular parent category relationship detected.")
                visited.add(curr)
                parent_node = db.get(Category, curr)
                curr = parent_node.parent_id if parent_node else None

            category.parent_id = payload.parent_id

        if payload.is_active is not None:
            category.is_active = payload.is_active

        db.commit()
        db.refresh(category)
        return CategoryResponse.model_validate(category)

    @staticmethod
    def delete_category(db: Session, business_id: uuid.UUID, category_id: uuid.UUID) -> dict[str, str]:
        """Safely deactivates or removes a category if unreferenced."""
        category = db.scalar(select(Category).where(Category.id == category_id, Category.business_id == business_id))
        if not category:
            raise EntityNotFound("Category not found in your catalogue.")

        if category.is_system:
            raise BusinessRuleViolation("System-defined categories cannot be deleted.")

        # Check if products reference this category
        prod_count = db.scalar(
            select(func.count(Product.id)).where(Product.category_id == category_id)
        ) or 0
        if prod_count > 0:
            category.is_active = False
            db.commit()
            return {"message": f"Category is referenced by {prod_count} product(s). Deactivated instead of deleted."}

        # Check if subcategories reference this category
        sub_count = db.scalar(
            select(func.count(Category.id)).where(Category.parent_id == category_id)
        ) or 0
        if sub_count > 0:
            category.is_active = False
            db.commit()
            return {"message": f"Category has {sub_count} subcategories. Deactivated instead of deleted."}

        db.delete(category)
        db.commit()
        return {"message": "Category deleted successfully."}

    # -------------------------------------------------------------------------
    # Products
    # -------------------------------------------------------------------------
    @staticmethod
    def create_product(db: Session, business_id: uuid.UUID, payload: ProductCreate) -> ProductResponse:
        """
        Creates a new product with optional single/multi-variant configuration and barcodes.
        Enforces tenant SKU uniqueness, barcode uniqueness, and decimal price invariants.
        """
        # Validate SKU uniqueness across business
        existing_sku = db.scalar(
            select(Product).where(Product.business_id == business_id, Product.sku == payload.sku)
        )
        if existing_sku:
            raise BusinessRuleViolation(f"Product with SKU '{payload.sku}' already exists in your catalogue.")

        # Validate variant SKUs
        for v in payload.variants:
            if v.sku == payload.sku:
                raise BusinessRuleViolation(f"Variant SKU '{v.sku}' cannot be identical to master product SKU.")
            var_exists = db.scalar(
                select(ProductVariant).where(ProductVariant.business_id == business_id, ProductVariant.sku == v.sku)
            )
            if var_exists:
                raise BusinessRuleViolation(f"Variant with SKU '{v.sku}' already exists.")

        # Validate Category ownership
        if payload.category_id:
            cat = db.scalar(select(Category).where(
                Category.id == payload.category_id,
                or_(Category.business_id == business_id, Category.is_system.is_(True)),
            ))
            if not cat:
                raise ValidationFailure("Selected category does not exist in your catalogue.")

        # Validate Brand ownership
        if payload.brand_id:
            brand = db.scalar(select(Brand).where(Brand.id == payload.brand_id, Brand.business_id == business_id))
            if not brand:
                raise ValidationFailure("Selected brand does not exist in your catalogue.")

        # Validate Base UOM
        uom = db.get(UnitOfMeasure, payload.base_uom_id)
        if not uom:
            raise ValidationFailure("Selected unit of measure does not exist.")

        # Validate all Barcodes uniqueness across business
        all_barcodes = list(payload.barcodes)
        for v in payload.variants:
            all_barcodes.extend(v.barcodes)

        if len(all_barcodes) != len(set(all_barcodes)):
            raise ValidationFailure("Duplicate barcodes provided in the product request.")

        for b in all_barcodes:
            bc_exists = db.scalar(select(ProductBarcode).where(ProductBarcode.business_id == business_id, ProductBarcode.barcode == b))
            if bc_exists:
                raise BusinessRuleViolation(f"Barcode '{b}' is already registered to another item in your catalogue.")

        product = Product(
            business_id=business_id,
            category_id=payload.category_id,
            brand_id=payload.brand_id,
            name=payload.name,
            description=payload.description,
            image_url=payload.image_url,
            sku=payload.sku,
            hsn_code=payload.hsn_code,
            base_uom_id=payload.base_uom_id,
            selling_price=payload.selling_price,
            mrp=payload.mrp,
            cost_price=payload.cost_price,
            tax_rate_percent=payload.tax_rate_percent,
            is_tax_inclusive=payload.is_tax_inclusive,
            reorder_threshold=payload.reorder_threshold,
            is_loose_item=payload.is_loose_item,
            has_variants=bool(payload.variants),
            is_active=True,
        )
        db.add(product)
        db.flush()

        # Attach master product barcodes
        for idx, bc in enumerate(payload.barcodes):
            product_barcode = ProductBarcode(
                business_id=business_id,
                product_id=product.id,
                variant_id=None,
                barcode=bc,
                is_primary=(idx == 0),
            )
            db.add(product_barcode)

        # Attach variants
        for v in payload.variants:
            v_uom = db.get(UnitOfMeasure, v.base_uom_id)
            if not v_uom:
                raise ValidationFailure(f"UOM for variant '{v.variant_name}' not found.")

            variant = ProductVariant(
                business_id=business_id,
                product_id=product.id,
                variant_name=v.variant_name,
                sku=v.sku,
                base_uom_id=v.base_uom_id,
                cost_price=v.cost_price,
                selling_price=v.selling_price,
                mrp=v.mrp,
                tax_rate_percent=v.tax_rate_percent,
                is_tax_inclusive=v.is_tax_inclusive,
                is_active=v.is_active,
            )
            db.add(variant)
            db.flush()

            for idx, bc in enumerate(v.barcodes):
                v_barcode = ProductBarcode(
                    business_id=business_id,
                    product_id=product.id,
                    variant_id=variant.id,
                    barcode=bc,
                    is_primary=(idx == 0),
                )
                db.add(v_barcode)

        db.commit()
        return CatalogueService.get_product(db, business_id, product.id)

    @staticmethod
    def get_product(db: Session, business_id: uuid.UUID, product_id: uuid.UUID) -> ProductResponse:
        """Retrieves a single product with full relational metadata."""
        stmt = (
            select(Product)
            .where(Product.id == product_id, Product.business_id == business_id)
            .options(
                joinedload(Product.category),
                joinedload(Product.brand),
                joinedload(Product.base_uom),
                selectinload(Product.barcodes),
                selectinload(Product.variants).selectinload(ProductVariant.barcodes),
                selectinload(Product.variants).joinedload(ProductVariant.base_uom),
            )
        )
        product = db.scalar(stmt)
        if not product:
            raise EntityNotFound("Product not found in your business catalogue.")
        return ProductResponse.model_validate(product)

    @staticmethod
    def list_products(
        db: Session,
        business_id: uuid.UUID,
        search: str | None = None,
        category_id: uuid.UUID | None = None,
        brand_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at_desc",
    ) -> ProductListResponse:
        """
        Queries catalogue products with pagination, case-insensitive search, and multi-faceted filtering.
        """
        page = max(1, page)
        page_size = max(1, min(page_size, 100))

        conditions = [Product.business_id == business_id]

        if is_active is not None:
            conditions.append(Product.is_active.is_(is_active))
        if category_id:
            conditions.append(Product.category_id == category_id)
        if brand_id:
            conditions.append(Product.brand_id == brand_id)

        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            # Search in product name, master sku, or barcodes
            barcode_subquery = (
                select(ProductBarcode.product_id)
                .where(ProductBarcode.business_id == business_id, ProductBarcode.barcode.ilike(term))
            )
            conditions.append(
                or_(
                    func.lower(Product.name).like(term),
                    func.lower(Product.sku).like(term),
                    Product.id.in_(barcode_subquery),
                )
            )

        # Count total
        count_stmt = select(func.count(Product.id)).where(and_(*conditions))
        total = db.scalar(count_stmt) or 0

        # Query items
        stmt = (
            select(Product)
            .where(and_(*conditions))
            .options(
                joinedload(Product.category),
                joinedload(Product.brand),
                joinedload(Product.base_uom),
                selectinload(Product.barcodes),
                selectinload(Product.variants).selectinload(ProductVariant.barcodes),
                selectinload(Product.variants).joinedload(ProductVariant.base_uom),
            )
        )

        if sort_by == "name_asc":
            stmt = stmt.order_by(Product.name.asc())
        elif sort_by == "name_desc":
            stmt = stmt.order_by(Product.name.desc())
        elif sort_by == "price_asc":
            stmt = stmt.order_by(Product.selling_price.asc())
        elif sort_by == "price_desc":
            stmt = stmt.order_by(Product.selling_price.desc())
        else:
            stmt = stmt.order_by(Product.created_at.desc())

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        items = db.scalars(stmt).unique().all()

        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return ProductListResponse(
            items=[ProductResponse.model_validate(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=total_pages,
        )

    @staticmethod
    def update_product(
        db: Session,
        business_id: uuid.UUID,
        product_id: uuid.UUID,
        payload: ProductUpdate,
    ) -> ProductResponse:
        """Updates product metadata and pricing in accordance with legal and retail constraints."""
        product = db.scalar(select(Product).where(Product.id == product_id, Product.business_id == business_id))
        if not product:
            raise EntityNotFound("Product not found.")

        if payload.sku and payload.sku != product.sku:
            existing = db.scalar(select(Product).where(
                Product.business_id == business_id,
                Product.sku == payload.sku,
                Product.id != product_id,
            ))
            if existing:
                raise BusinessRuleViolation(f"SKU '{payload.sku}' is already assigned to another product.")
            product.sku = payload.sku

        if payload.category_id is not None:
            cat = db.scalar(select(Category).where(
                Category.id == payload.category_id,
                or_(Category.business_id == business_id, Category.is_system.is_(True)),
            ))
            if not cat:
                raise ValidationFailure("Selected category does not exist.")
            product.category_id = payload.category_id

        if payload.brand_id is not None:
            brand = db.scalar(select(Brand).where(Brand.id == payload.brand_id, Brand.business_id == business_id))
            if not brand:
                raise ValidationFailure("Selected brand does not exist.")
            product.brand_id = payload.brand_id

        if payload.base_uom_id is not None:
            uom = db.get(UnitOfMeasure, payload.base_uom_id)
            if not uom:
                raise ValidationFailure("Selected unit of measure does not exist.")
            product.base_uom_id = payload.base_uom_id

        # Update pricing with atomic validation
        new_sp = payload.selling_price if payload.selling_price is not None else product.selling_price
        new_mrp = payload.mrp if payload.mrp is not None else product.mrp
        if new_sp > new_mrp:
            raise BusinessRuleViolation(f"Selling price ({new_sp}) cannot exceed MRP ({new_mrp}).")

        if payload.name is not None:
            product.name = payload.name
        if payload.description is not None:
            product.description = payload.description
        if payload.image_url is not None:
            product.image_url = payload.image_url
        if payload.hsn_code is not None:
            product.hsn_code = payload.hsn_code
        if payload.selling_price is not None:
            product.selling_price = payload.selling_price
        if payload.mrp is not None:
            product.mrp = payload.mrp
        if payload.cost_price is not None:
            product.cost_price = payload.cost_price
        if payload.tax_rate_percent is not None:
            product.tax_rate_percent = payload.tax_rate_percent
        if payload.is_tax_inclusive is not None:
            product.is_tax_inclusive = payload.is_tax_inclusive
        if payload.reorder_threshold is not None:
            product.reorder_threshold = payload.reorder_threshold
        if payload.is_loose_item is not None:
            product.is_loose_item = payload.is_loose_item
        if payload.is_active is not None:
            product.is_active = payload.is_active

        db.commit()
        return CatalogueService.get_product(db, business_id, product.id)

    @staticmethod
    def deactivate_product(db: Session, business_id: uuid.UUID, product_id: uuid.UUID) -> dict[str, str]:
        """Soft-deactivates a product and its variants to maintain historical integrity."""
        product = db.scalar(select(Product).where(Product.id == product_id, Product.business_id == business_id))
        if not product:
            raise EntityNotFound("Product not found.")

        product.is_active = False
        for v in product.variants:
            v.is_active = False

        db.commit()
        return {"message": "Product deactivated successfully."}

    # -------------------------------------------------------------------------
    # Variants Management
    # -------------------------------------------------------------------------
    @staticmethod
    def create_variant(
        db: Session,
        business_id: uuid.UUID,
        product_id: uuid.UUID,
        payload: ProductVariantCreate,
    ) -> ProductVariantResponse:
        """Adds a variant to a product."""
        product = db.scalar(select(Product).where(Product.id == product_id, Product.business_id == business_id))
        if not product:
            raise EntityNotFound("Product not found.")

        # Check SKU uniqueness
        sku_exists = db.scalar(select(ProductVariant).where(ProductVariant.business_id == business_id, ProductVariant.sku == payload.sku))
        if sku_exists:
            raise BusinessRuleViolation(f"Variant SKU '{payload.sku}' already exists.")

        # Check Barcodes uniqueness
        for bc in payload.barcodes:
            bc_exists = db.scalar(select(ProductBarcode).where(ProductBarcode.business_id == business_id, ProductBarcode.barcode == bc))
            if bc_exists:
                raise BusinessRuleViolation(f"Barcode '{bc}' already exists in your catalogue.")

        variant = ProductVariant(
            business_id=business_id,
            product_id=product.id,
            variant_name=payload.variant_name,
            sku=payload.sku,
            base_uom_id=payload.base_uom_id,
            cost_price=payload.cost_price,
            selling_price=payload.selling_price,
            mrp=payload.mrp,
            tax_rate_percent=payload.tax_rate_percent,
            is_tax_inclusive=payload.is_tax_inclusive,
            is_active=payload.is_active,
        )
        db.add(variant)
        product.has_variants = True
        db.flush()

        for idx, bc in enumerate(payload.barcodes):
            product_barcode = ProductBarcode(
                business_id=business_id,
                product_id=product.id,
                variant_id=variant.id,
                barcode=bc,
                is_primary=(idx == 0),
            )
            db.add(product_barcode)

        db.commit()
        db.refresh(variant)
        return ProductVariantResponse.model_validate(variant)

    @staticmethod
    def list_variants(db: Session, business_id: uuid.UUID, product_id: uuid.UUID) -> list[ProductVariantResponse]:
        """Lists all variants for a given product."""
        stmt = (
            select(ProductVariant)
            .where(ProductVariant.product_id == product_id, ProductVariant.business_id == business_id)
            .options(
                joinedload(ProductVariant.base_uom),
                selectinload(ProductVariant.barcodes),
            )
            .order_by(ProductVariant.variant_name.asc())
        )
        variants = db.scalars(stmt).all()
        return [ProductVariantResponse.model_validate(v) for v in variants]

    @staticmethod
    def update_variant(
        db: Session,
        business_id: uuid.UUID,
        product_id: uuid.UUID,
        variant_id: uuid.UUID,
        payload: ProductVariantUpdate,
    ) -> ProductVariantResponse:
        """Updates a variant's metadata, SKU, or pricing."""
        variant = db.scalar(
            select(ProductVariant).where(
                ProductVariant.id == variant_id,
                ProductVariant.product_id == product_id,
                ProductVariant.business_id == business_id,
            )
        )
        if not variant:
            raise EntityNotFound("Product variant not found.")

        if payload.sku and payload.sku != variant.sku:
            exists = db.scalar(select(ProductVariant).where(
                ProductVariant.business_id == business_id,
                ProductVariant.sku == payload.sku,
                ProductVariant.id != variant_id,
            ))
            if exists:
                raise BusinessRuleViolation(f"Variant SKU '{payload.sku}' is already assigned.")
            variant.sku = payload.sku

        new_sp = payload.selling_price if payload.selling_price is not None else variant.selling_price
        new_mrp = payload.mrp if payload.mrp is not None else variant.mrp
        if new_sp > new_mrp:
            raise BusinessRuleViolation(f"Selling price ({new_sp}) cannot exceed MRP ({new_mrp}).")

        if payload.variant_name is not None:
            variant.variant_name = payload.variant_name
        if payload.base_uom_id is not None:
            variant.base_uom_id = payload.base_uom_id
        if payload.cost_price is not None:
            variant.cost_price = payload.cost_price
        if payload.selling_price is not None:
            variant.selling_price = payload.selling_price
        if payload.mrp is not None:
            variant.mrp = payload.mrp
        if payload.tax_rate_percent is not None:
            variant.tax_rate_percent = payload.tax_rate_percent
        if payload.is_tax_inclusive is not None:
            variant.is_tax_inclusive = payload.is_tax_inclusive
        if payload.is_active is not None:
            variant.is_active = payload.is_active

        db.commit()
        db.refresh(variant)
        return ProductVariantResponse.model_validate(variant)

    @staticmethod
    def deactivate_variant(db: Session, business_id: uuid.UUID, product_id: uuid.UUID, variant_id: uuid.UUID) -> dict[str, str]:
        """Soft-deactivates a product variant."""
        variant = db.scalar(select(ProductVariant).where(
            ProductVariant.id == variant_id,
            ProductVariant.product_id == product_id,
            ProductVariant.business_id == business_id,
        ))
        if not variant:
            raise EntityNotFound("Variant not found.")

        variant.is_active = False
        db.commit()
        return {"message": "Variant deactivated successfully."}

    # -------------------------------------------------------------------------
    # Barcodes
    # -------------------------------------------------------------------------
    @staticmethod
    def add_barcode(
        db: Session,
        business_id: uuid.UUID,
        product_id: uuid.UUID,
        payload: ProductBarcodeCreate,
    ) -> ProductBarcodeResponse:
        """Adds a barcode to a product or specific variant."""
        product = db.scalar(select(Product).where(Product.id == product_id, Product.business_id == business_id))
        if not product:
            raise EntityNotFound("Product not found.")

        existing = db.scalar(select(ProductBarcode).where(
            ProductBarcode.business_id == business_id,
            ProductBarcode.barcode == payload.barcode,
        ))
        if existing:
            raise BusinessRuleViolation(f"Barcode '{payload.barcode}' already registered.")

        if payload.variant_id:
            var = db.scalar(select(ProductVariant).where(
                ProductVariant.id == payload.variant_id,
                ProductVariant.product_id == product_id,
                ProductVariant.business_id == business_id,
            ))
            if not var:
                raise ValidationFailure("Variant does not belong to this product.")

        if payload.is_primary:
            # Set other barcodes for this product/variant to not primary
            if payload.variant_id:
                other_bcs = db.scalars(
                    select(ProductBarcode).where(
                        ProductBarcode.variant_id == payload.variant_id,
                        ProductBarcode.is_primary.is_(True),
                    )
                ).all()
            else:
                other_bcs = db.scalars(
                    select(ProductBarcode).where(
                        ProductBarcode.product_id == product_id,
                        ProductBarcode.variant_id.is_(None),
                        ProductBarcode.is_primary.is_(True),
                    )
                ).all()
            for b in other_bcs:
                b.is_primary = False

        barcode = ProductBarcode(
            business_id=business_id,
            product_id=product_id,
            variant_id=payload.variant_id,
            barcode=payload.barcode,
            barcode_type=payload.barcode_type,
            is_primary=payload.is_primary,
        )
        db.add(barcode)
        db.commit()
        db.refresh(barcode)
        return ProductBarcodeResponse.model_validate(barcode)

    @staticmethod
    def lookup_barcode(db: Session, business_id: uuid.UUID, barcode_value: str) -> BarcodeLookupResponse:
        """Fast indexed resolution of a scanned barcode to its product and variant."""
        clean_code = barcode_value.strip()
        stmt = (
            select(ProductBarcode)
            .where(
                ProductBarcode.business_id == business_id,
                ProductBarcode.barcode == clean_code,
            )
            .options(
                joinedload(ProductBarcode.product).joinedload(Product.category),
                joinedload(ProductBarcode.product).joinedload(Product.brand),
                joinedload(ProductBarcode.product).joinedload(Product.base_uom),
                joinedload(ProductBarcode.variant).joinedload(ProductVariant.base_uom),
            )
        )
        barcode_rec = db.scalar(stmt)
        if not barcode_rec:
            raise EntityNotFound(f"Barcode '{clean_code}' is not registered in your catalogue.")

        product_resp = CatalogueService.get_product(db, business_id, barcode_rec.product_id)
        variant_resp = ProductVariantResponse.model_validate(barcode_rec.variant) if barcode_rec.variant else None

        return BarcodeLookupResponse(
            barcode=barcode_rec.barcode,
            barcode_type=barcode_rec.barcode_type,
            product=product_resp,
            variant=variant_resp,
        )
