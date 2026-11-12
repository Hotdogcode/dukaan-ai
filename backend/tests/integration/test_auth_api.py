"""
Integration Tests for Authentication API: OTP flow, JWT issuing, rotation, and logout.
"""

import pytest
from httpx import AsyncClient

from backend.app.infrastructure.otp.dev_provider import DevOTPProvider
from backend.app.infrastructure.otp.service import OTPService


@pytest.mark.asyncio
async def test_full_otp_authentication_flow(client: AsyncClient):
    """End-to-end test: Request OTP -> Verify OTP -> Get Tokens -> Query /auth/me."""
    phone = "9876543210"

    # 1. Request OTP
    req_resp = await client.post("/api/v1/auth/request-otp", json={"phone_number": phone})
    assert req_resp.status_code == 200
    req_data = req_resp.json()
    assert req_data["phone_number"] == "+919876543210"
    assert "X-Request-ID" in req_resp.headers

    # Retrieve dispatched code from dev provider
    provider = OTPService.get_provider()
    assert isinstance(provider, DevOTPProvider)
    otp_code = provider.get_latest_otp("+919876543210")
    assert otp_code is not None

    # 2. Verify OTP & Register New Merchant
    verify_resp = await client.post(
        "/api/v1/auth/verify-otp",
        json={
            "phone_number": phone,
            "otp": otp_code,
            "full_name": "Ramesh Kumar",
            "device_fingerprint": "terminal-test-001",
        },
    )
    assert verify_resp.status_code == 200
    tokens = verify_resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["user"]["full_name"] == "Ramesh Kumar"
    assert tokens["user"]["phone_number"] == "+919876543210"

    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # 3. Query Protected /auth/me Endpoint
    headers = {"Authorization": f"Bearer {access_token}"}
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["full_name"] == "Ramesh Kumar"
    assert me_data["phone_number"] == "+919876543210"

    # 4. Rotate Refresh Token
    refresh_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert new_tokens["access_token"] != access_token
    assert new_tokens["refresh_token"] != refresh_token

    # 5. Old Refresh Token Must Be Revoked (Reuse Detection)
    reuse_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse_resp.status_code == 401
    assert "reuse detected" in reuse_resp.json()["error"]["message"].lower()

    # 6. Logout
    logout_resp = await client.post("/api/v1/auth/logout", json={"refresh_token": new_tokens["refresh_token"]})
    assert logout_resp.status_code == 200

    # 7. Access with revoked session fails
    revoked_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_tokens['access_token']}"})
    assert revoked_resp.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(client: AsyncClient):
    """Requests without valid Bearer tokens must return 401."""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    err = resp.json()["error"]
    assert err["code"] == "AUTHENTICATION_REQUIRED"
    assert "request_id" in err


@pytest.mark.asyncio
async def test_invalid_otp_returns_error_envelope(client: AsyncClient):
    """Submitting incorrect OTP returns standardized 400 response."""
    phone = "9811122233"
    await client.post("/api/v1/auth/request-otp", json={"phone_number": phone})

    verify_resp = await client.post(
        "/api/v1/auth/verify-otp",
        json={"phone_number": phone, "otp": "999999"},
    )
    assert verify_resp.status_code == 400
    err = verify_resp.json()["error"]
    assert err["code"] == "INVALID_OTP"
    assert "remaining" in err["message"].lower()
