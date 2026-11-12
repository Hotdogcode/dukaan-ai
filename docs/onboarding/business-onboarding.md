# DukaanAI — Business Onboarding Architecture

## 1. Overview
When a newly registered merchant completes OTP verification, DukaanAI inspects their business memberships. If the merchant has no business (`businesses.isEmpty()`), the application immediately initiates the business onboarding sequence.

---

## 2. Onboarding Workflow

```mermaid
flowchart TD
    Start([Merchant Logs In]) --> CheckBiz{Active Businesses?}
    CheckBiz -- Yes --> Dashboard[Navigate to Dashboard]
    CheckBiz -- No --> OnboardingForm[Display Business Onboarding Screen]
    
    OnboardingForm --> InputDetails["Capture: Business Name, Business Category, Owner Name, Preferred Language, Primary Store Details"]
    InputDetails --> Validate{Valid Input?}
    Validate -- No --> DisplayError[Show Validation Feedback]
    Validate -- Yes --> CallAPI[POST /api/v1/businesses]
    
    CallAPI --> CreateDB["Atomic Transaction:
    1. Create Business Record
    2. Add User as OWNER
    3. Provision Primary Store (is_primary = true)"]
    
    CreateDB --> CacheContext["Store Active Context in DataStore:
    - selectedBusinessId
    - selectedStoreId
    - selectedBusinessName
    - userRole = 'OWNER'"]
    
    CacheContext --> Complete[Navigate to Dashboard]
```

---

## 3. Business Types & Categories
DukaanAI supports common Indian small retail formats:
- **GROCERY (किराना):** General FMCG, packed groceries, spices, grains.
- **GENERAL (जनरल स्टोर):** Stationery, toiletries, small household goods.
- **DAIRY (डेयरी):** Milk, curd, paneer, and perishables.
- **PHARMACY (दवाखाना):** Chemist and OTC healthcare.
- **OTHER:** Custom retail.
