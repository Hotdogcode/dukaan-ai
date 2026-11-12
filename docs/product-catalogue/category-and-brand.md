# Category and Brand Architecture

## 1. Category Hierarchy Design
Categories allow merchants to organize inventory logically (e.g. Grocery -> Flours -> Atta, Beverages -> Tea).

### Hierarchy Support:
- Each category optionally points to a `parent_id` (self-referencing foreign key).
- Root categories have `parent_id = NULL`.
- Category cycle prevention is strictly enforced in `CatalogueService.create_category` and `CatalogueService.update_category`:
  - A category cannot be its own parent (`parent_id != id`).
  - An ancestor node cannot be set as a child of any of its descendants.

### System Defaults vs Custom Categories:
- **System Categories:** `business_id IS NULL, is_system = TRUE` (e.g. Grocery, Dairy, Beverages, Snacks, Personal Care, Household, Stationery). These are read-only for standard users and visible to all businesses.
- **Tenant Categories:** `business_id = <business_uuid>, is_system = FALSE`. Merchants can create, edit, sort, and deactivate their custom categories.

## 2. Brand Architecture
Brands represent manufacturers or product lines (e.g., "Amul", "Parle", "Tata", "Nestle", "Patanjali", "Britannia").
- Scoped to `(business_id, name)` with case-insensitive unique constraint.
- Supports optional logo URLs and descriptions.
- Soft-deletion via `is_active`.
- Filterable and searchable via API `/api/v1/brands` and local Room cache `brands`.
