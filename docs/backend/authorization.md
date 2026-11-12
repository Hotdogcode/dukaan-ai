# DukaanAI — Authorization & Role-Based Permissions

## 1. Permission-Based Authorization Philosophy

DukaanAI avoids scattering hardcoded role checks (`if user.role == 'OWNER'`) throughout route handlers. Instead, the system uses a **Centralized Permission-Based Authorization Model**:
- Handlers declare the exact capability required (e.g. `business.update`, `sales.create`, `members.manage`).
- Roles are treated as collections of granular permissions.
- Changing permissions for a role requires updating a single central dictionary without modifying any API routes.

---

## 2. Granular Permissions Registry

| Permission Code | Description | Domain Scope |
|---|---|---|
| `business.read` | View business settings, profile, and member list | Business Context |
| `business.update` | Update trade name, GSTIN, and settings | Business Context |
| `members.manage` | Add, update, or remove staff members and roles | Membership |
| `products.read` | Browse and search catalog products and barcodes | Catalogue |
| `products.write` | Create SKUs, edit pricing, and update MRP | Catalogue |
| `sales.read` | View past sales invoices and shift history | Sales |
| `sales.create` | Perform POS counter checkout and issue invoices | Sales |
| `inventory.read` | View on-hand stock balances and movements | Inventory |
| `inventory.adjust` | Conduct physical counts and approve variances | Inventory |
| `finance.read` | View cash register drawers and expense reports | Financials |
| `reports.read` | View business analytics and performance dashboards | Intelligence |

---

## 3. Role-to-Permission Matrix

| Permission | OWNER | MANAGER | CASHIER | INVENTORY_STAFF |
|---|:---:|:---:|:---:|:---:|
| `business.read` | ✅ | ✅ | ✅ | ✅ |
| `business.update` | ✅ | ✅ | ❌ | ❌ |
| `members.manage` | ✅ | ✅ | ❌ | ❌ |
| `products.read` | ✅ | ✅ | ✅ | ✅ |
| `products.write` | ✅ | ✅ | ❌ | ✅ |
| `sales.read` | ✅ | ✅ | ✅ | ❌ |
| `sales.create` | ✅ | ✅ | ✅ | ❌ |
| `inventory.read` | ✅ | ✅ | ❌ | ✅ |
| `inventory.adjust` | ✅ | ✅ | ❌ | ✅ |
| `finance.read` | ✅ | ✅ | ✅ | ❌ |
| `reports.read` | ✅ | ✅ | ❌ | ❌ |

---

## 4. Implementation in FastAPI Endpoints

Route protection is achieved by composing dependencies:

```python
from fastapi import APIRouter, Depends
from backend.app.api.dependencies import get_current_user, require_permission
from backend.app.core.security import Permissions

router = APIRouter(prefix="/businesses/{business_id}")

@router.patch("")
def update_business_settings(
    business_id: uuid.UUID,
    payload: BusinessUpdate,
    current_user: User = Depends(get_current_user),
    # 1. Authoritatively asserts user belongs to business_id
    # 2. Sets PostgreSQL RLS context
    # 3. Asserts user's role has BUSINESS_UPDATE permission
    _membership = Depends(require_permission(Permissions.BUSINESS_UPDATE)),
    db: Session = Depends(get_db_session),
):
    ...
```

If a user with role `CASHIER` attempts to hit this endpoint, the dependency halts execution before the service layer is reached, returning:
```json
{
  "error": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "message": "Insufficient permissions to perform this operation. Required: business.update",
    "request_id": "...",
    "details": [{"required_permission": "business.update"}]
  }
}
```
