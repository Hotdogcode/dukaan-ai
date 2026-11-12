# Multi-Tenancy Architecture

## Overview
DukaanAI is an Indian retail and kirana store management platform architected as a pooled multi-tenant SaaS. Multiple retail businesses share the same application cluster and database engine while maintaining strict logical and physical data isolation.

## Tenancy Model: Shared Process & Pooled Database with Logical Isolation
- **Tenant Entity**: The tenant boundary is rooted at the `Business` aggregate (`business_id` UUID).
- **Sub-Tenancy (Store Hierarchy)**: A business can own one or more retail stores (`Store` entity with `store_id` UUID and foreign key `business_id`).
- **Data Model Segregation**: Every business-owned entity (products, inventory movements, sales orders, khata transactions, financial entries, etc.) contains a mandatory, non-nullable `business_id` column.

## Isolation Enforcement Layers

### 1. Application-Level Scoping & JWT Validation
Every API endpoint operating on business resources requires the `X-Business-ID` header. The dependency `get_tenant_membership` in `backend.app.api.dependencies.auth`:
1. Validates the caller's JWT access token.
2. Reads the `X-Business-ID` request header and verifies its UUID format.
3. Queries `business_users` to verify active membership (`is_active = True`).
4. Extracts and assigns the user's explicit role (`OWNER`, `MANAGER`, `CASHIER`, `INVENTORY_STAFF`).
5. Rejects any caller attempting to access a business where they are not an active member with `HTTP 403 Forbidden` (`FORBIDDEN_BUSINESS_ACCESS`).

### 2. PostgreSQL Row-Level Security (RLS)
To guarantee defense-in-depth against accidental omission of `WHERE business_id = :id` filters:
- In production PostgreSQL, PostgreSQL Row-Level Security (RLS) policies are defined on all tenant-owned tables:
  ```sql
  ALTER TABLE products ENABLE ROW LEVEL SECURITY;
  CREATE POLICY tenant_isolation_policy ON products
      USING (business_id = NULLIF(current_setting('app.current_business_id', true), '')::uuid);
  ```
- Before executing business queries, the database session dependency executes:
  ```python
  await session.execute(
      text("SET LOCAL app.current_business_id = :business_id"),
      {"business_id": str(business_id)},
  )
  ```
- This ensures that even if an SQL query lacks an explicit `WHERE business_id = ...` predicate, the database engine filters out all records belonging to other tenants.
- Superadmin queries or system background jobs explicitly run with system privileges when tenant-agnostic aggregation is required.

### 3. Repository and Query Contract
- All repository methods explicitly accept and require `business_id: UUID`.
- Composite indexes with `business_id` as the leading column (e.g., `(business_id, barcode)`, `(business_id, phone_number)`) optimize lookups and guarantee unique constraints are scoped strictly per tenant.

## Cross-Tenant Protection & Testing
Our automated test suite includes dedicated security tests (`tests/security/test_tenant_authorization.py`) that verify:
1. User A belonging to Business 1 cannot read, modify, or list Business 2's resources.
2. Spoofed `X-Business-ID` headers are intercepted and rejected with `403 Forbidden`.
3. Inactive or revoked members cannot access tenant endpoints.
