# DukaanAI — Store Outlets API Reference

## 1. Create Store Outlet
- **Endpoint:** `POST /api/v1/businesses/{business_id}/stores`
- **Headers:** `Authorization: Bearer <access_token>`, `X-Business-ID: {business_id}`
- **Required Permission:** `business.update`
- **Request Body:**
```json
{
  "name": "Gupta Kirana Express Outlet",
  "code": "EXP01",
  "address_line1": "Shop 4, Station Road",
  "city": "Mumbai",
  "state": "Maharashtra",
  "pincode": "400050",
  "phone_number": "9876543210",
  "is_primary": true,
  "timezone": "Asia/Kolkata"
}
```
- **Response (201 Created):**
```json
{
  "id": "e0b9d628-91c2-482f-8186-0bf17b70c321",
  "business_id": "c1f7605e-8559-4d62-8717-386f5628b001",
  "name": "Gupta Kirana Express Outlet",
  "code": "EXP01",
  "address_line1": "Shop 4, Station Road",
  "address_line2": null,
  "city": "Mumbai",
  "state": "Maharashtra",
  "pincode": "400050",
  "phone_number": "9876543210",
  "is_primary": true,
  "timezone": "Asia/Kolkata",
  "is_active": true,
  "created_at": "2026-11-12T10:05:00Z"
}
```

---

## 2. List Store Outlets
- **Endpoint:** `GET /api/v1/businesses/{business_id}/stores`
- **Headers:** `Authorization: Bearer <access_token>`, `X-Business-ID: {business_id}`
- **Required Permission:** `business.read`
- **Response (200 OK):** Array of `StoreResponse` objects, ordered with `is_primary = true` first.

---

## 3. Get Store Outlet Details
- **Endpoint:** `GET /api/v1/businesses/{business_id}/stores/{store_id}`
- **Headers:** `Authorization: Bearer <access_token>`, `X-Business-ID: {business_id}`
- **Response (200 OK):** Verified `StoreResponse` object.

---

## 4. Update Store Outlet
- **Endpoint:** `PATCH /api/v1/businesses/{business_id}/stores/{store_id}`
- **Headers:** `Authorization: Bearer <access_token>`, `X-Business-ID: {business_id}`
- **Required Permission:** `business.update`
- **Request Body:** Partial store updates. If `is_primary: true` is passed, any other primary store for the business is atomically updated to `is_primary = false`.
