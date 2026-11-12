# Product Domain Architecture & Bounded Context

## 1. Domain Overview
In DukaanAI, the **Product Catalogue Domain** represents the foundational bounded context for all inventory, cataloguing, and point-of-sale activities within a retail store (kirana, general grocery, FMCG).

The domain models items sold by a retail business, their variations (weight, pack size), hierarchical categories, brands, standardized units of measure (UOM), and barcode mappings.

## 2. Core Entities & Aggregate Roots

### Product (Aggregate Root)
The `Product` entity represents a sellable catalog item.
- **Identity:** `id` (UUIDv7 / UUID).
- **Tenant Scope:** `business_id` (mandatory, multi-tenant isolation via PostgreSQL Row Level Security).
- **Core Attributes:**
  - `name`: Primary product name (e.g. "Parle-G Glucose Biscuits").
  - `brand_id`: Foreign key to `brands.id` (optional).
  - `category_id`: Foreign key to `categories.id` (optional).
  - `description`: Textual notes or marketing description.
  - `is_active`: Soft-deletion / archival state flag.
  - `has_variants`: Boolean indicating if product contains multiple variations or a single default variant.
- **Invariants:**
  - Every product belongs to exactly one `business_id`.
  - Simple products without explicit multiple variations have exactly one default `ProductVariant`.
  - Inactive products do not appear in normal billing or search unless explicitly requested.

### ProductVariant (Entity)
Represents a concrete sellable SKU of a product (e.g., 50g, 100g, 250g, 1kg).
- **Attributes:**
  - `variant_name`: Human-readable name (e.g. "100 g", "Economy Pack").
  - `sku`: Unique stock keeping unit code scoped to business (`business_id, sku`).
  - `purchase_price`: Wholesale / buying cost (`Decimal(12, 4)`).
  - `selling_price`: Retail selling price (`Decimal(12, 4)`).
  - `mrp`: Maximum Retail Price printed on package (`Decimal(12, 4)`).
  - `unit_id`: Foreign key to `units_of_measure.id`.
  - `tax_rate`: GST rate (e.g. 0%, 5%, 12%, 18%, 28%).
  - `hsn_code`: Harmonized System of Nomenclature code for Indian GST compliance.
  - `is_default`: Boolean marking primary variant for simple product displays.
  - `is_active`: Boolean status.
- **Invariants:**
  - `selling_price <= mrp` (selling price cannot exceed printed MRP under Indian Consumer Protection rules).
  - `selling_price >= 0`, `purchase_price >= 0`, `mrp >= 0`.
  - When `purchase_price` is entered, `selling_price` is typically `>= purchase_price` (warning or policy check).

### ProductBarcode (Entity)
Supports 1-to-many barcode aliases per variant (EAN-13, UPC-A, Code-128, internal generated barcodes).
- Scoped to `(business_id, barcode)` for uniqueness.
- Tracks `is_primary` flag for barcode label printing.

## 3. Separation of Concerns
The catalogue domain models **what is sellable** (definitions, prices, barcodes, units, categories). It explicitly delegates:
- **Inventory/Stock Balances:** To the Stock Management Bounded Context (`inventory_levels`, `stock_ledger_entries`).
- **Orders/Invoices:** To the Sales Bounded Context.
- **Ledgers/Khata:** To the Khata Bounded Context.
