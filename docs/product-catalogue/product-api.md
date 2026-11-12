# Product Catalogue REST API Specification

## 1. Overview
Base URL: `https://dukaanai-backend-yx5b.onrender.com/api/v1` (Production Render Deployment).
Authentication: Bearer JWT (`Authorization: Bearer <token>`).
Multi-tenancy: Implicitly resolved from authenticated user's current business context or explicit header `X-Business-ID: <uuid>` enforced by PostgreSQL RLS.

## 2. Endpoints Summary

### Products
- `POST /products`: Create product with initial variant and optional barcode.
- `GET /products`: List products with filtering (`query`, `category_id`, `brand_id`, `include_inactive`, `page`, `page_size`).
- `GET /products/{product_id}`: Retrieve full product aggregate with variants and barcodes.
- `PUT /products/{product_id}`: Update product metadata.
- `DELETE /products/{product_id}`: Soft-delete / deactivate product.

### Product Variants
- `POST /products/{product_id}/variants`: Create a new variant for a product.
- `GET /products/{product_id}/variants`: List all variants for a product.
- `GET /variants/{variant_id}`: Get variant details.
- `PUT /variants/{variant_id}`: Update variant pricing, MRP, tax rate, SKU.
- `DELETE /variants/{variant_id}`: Soft-deactivate variant.

### Categories
- `POST /categories`: Create business category (validates cycle prevention).
- `GET /categories`: List categories (supports `include_system=true` and `parent_id` filter).
- `GET /categories/{category_id}`: Get category details.
- `PUT /categories/{category_id}`: Update category (name, code, display order, parent).
- `DELETE /categories/{category_id}`: Soft-delete category.

### Brands
- `POST /brands`: Create a brand.
- `GET /brands`: List brands.
- `GET /brands/{brand_id}`: Get brand details.
- `PUT /brands/{brand_id}`: Update brand.
- `DELETE /brands/{brand_id}`: Soft-delete brand.

### Barcodes
- `GET /barcodes/lookup?barcode={barcode}`: Fast O(1) lookup across business items.
- `POST /barcodes`: Register/associate a barcode with a variant.

### Units of Measure
- `GET /units`: List standard measurement units (kg, g, L, ml, pc, pack, box, etc.).
- `GET /units/conversions`: List conversion factors between units.
