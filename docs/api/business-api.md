# DukaanAI — Business API Reference

## 1. Create Business
- **Endpoint:** `POST /api/v1/businesses`
- **Headers:** `Authorization: Bearer <access_token>`
- **Summary:** Registers a new business tenant and automatically creates the primary store and OWNER role.
- **Request Body:**
```json
{
  "name": "Gupta Kirana Store",
  "business_type": "GROCERY",
  "owner_name": "Ramesh Gupta",
  "legal_name": "Gupta Retail Enterprises",
  "gstin": "27AAAAA0000A1Z5",
  "primary_language": "hi",
  "initial_store_name": "Main Market Branch"
}
```
- **Response (201 Created):**
```json
{
  "business": {
    "id": "c1f7605e-8559-4d62-8717-386f5628b001",
    "name": "Gupta Kirana Store",
    "business_type": "GROCERY",
    "owner_name": "Ramesh Gupta",
    "legal_name": "Gupta Retail Enterprises",
    "gstin": "27AAAAA0000A1Z5",
    "currency": "INR",
    "timezone": "Asia/Kolkata",
    "primary_language": "hi",
    "is_active": true,
    "created_at": "2026-11-12T10:00:00Z"
  },
  "role": "OWNER",
  "is_active": true,
  "permissions": ["business.read", "business.update", "members.manage"]
}
```

---

## 2. List User Businesses
- **Endpoint:** `GET /api/v1/businesses`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response (200 OK):** Array of `BusinessMembershipResponse` objects.

---

## 3. Get Business Details
- **Endpoint:** `GET /api/v1/businesses/{business_id}`
- **Headers:** `Authorization: Bearer <access_token>`, `X-Business-ID: {business_id}`
- **Response (200 OK):** `BusinessResponse` object.

---

## 4. Update Business Details
- **Endpoint:** `PATCH /api/v1/businesses/{business_id}`
- **Headers:** `Authorization: Bearer <access_token>`, `X-Business-ID: {business_id}`
- **Required Permission:** `business.update`
- **Request Body:** Partial fields (e.g., `{"name": "Gupta Super Kirana"}`).
