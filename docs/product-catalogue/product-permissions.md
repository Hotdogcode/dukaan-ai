# Product Permissions and Multi-Tenant Isolation

## 1. Multi-Tenant Isolation (Row-Level Security)
Every catalogue entity (`products`, `product_variants`, `product_barcodes`, `categories`, `brands`) carries a mandatory `business_id` UUID column.

PostgreSQL enforces isolation using Row Level Security policies:
```sql
CREATE POLICY product_tenant_isolation_policy ON products
FOR ALL USING (
    business_id = NULLIF(current_setting('app.current_business_id', true), '')::UUID
);
```
Even if a developer writes an unconstrained query (`SELECT * FROM products`), PostgreSQL guarantees that tenant data is unreachable by any unauthorized tenant.

## 2. Role-Based Access Control (RBAC)
Membership roles within a business:
- **OWNER / ADMIN:** Full CRUD rights on products, variants, categories, brands, price overrides, and tax settings.
- **MANAGER:** Can add products, adjust selling prices within limits, manage categories and barcodes.
- **CASHIER / STAFF:** Read-only access to catalogue for billing and barcode scanning. Cannot alter base selling price, MRP, or deactivate catalogue items.
