import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ApiError
from app.db.models import AppUser
from app.schemas.auth import ClerkClaims
from app.services.auth_service import AuthService
from app.services.user_service import UserService


def test_users_me_requires_authorization(client):
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_users_me_rejects_invalid_token(client):
    response = client.get("/api/v1/users/me", headers={"Authorization": "Bearer invalid"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_users_me_returns_current_user_with_mocked_clerk_claims(client, monkeypatch):
    claims = ClerkClaims(
        sub="user_123",
        email="user@example.com",
        first_name="Aman",
        last_name="Sharma",
        image_url="https://example.com/avatar.png",
    )
    user_id = uuid.uuid4()

    async def fake_verify_credentials(
        self: AuthService,
        credentials: HTTPAuthorizationCredentials | None,
    ) -> ClerkClaims:
        assert credentials is not None
        assert credentials.credentials == "valid"
        return claims

    async def fake_get_or_create(
        self: UserService,
        session: AsyncSession,
        received_claims: ClerkClaims,
    ) -> AppUser:
        assert received_claims == claims
        return AppUser(
            id=user_id,
            clerk_user_id=received_claims.clerk_user_id,
            email=received_claims.email,
            first_name=received_claims.first_name,
            last_name=received_claims.last_name,
            image_url=received_claims.image_url,
        )

    monkeypatch.setattr(AuthService, "verify_credentials", fake_verify_credentials)
    monkeypatch.setattr(UserService, "get_or_create_from_clerk_claims", fake_get_or_create)

    response = client.get("/api/v1/users/me", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "id": str(user_id),
            "email": "user@example.com",
            "first_name": "Aman",
            "last_name": "Sharma",
            "image_url": "https://example.com/avatar.png",
        }
    }


def test_users_me_creates_and_fetches_app_user_by_clerk_sub_without_email(client, monkeypatch):
    clerk_user_id = f"user_{uuid.uuid4().hex}"
    claims = ClerkClaims(
        sub=clerk_user_id,
        first_name="Local",
        last_name="Investigator",
        image_url=None,
    )

    async def fake_verify_credentials(
        self: AuthService,
        credentials: HTTPAuthorizationCredentials | None,
    ) -> ClerkClaims:
        assert credentials is not None
        assert credentials.credentials == "valid"
        return claims

    monkeypatch.setattr(AuthService, "verify_credentials", fake_verify_credentials)

    first_response = client.get("/api/v1/users/me", headers={"Authorization": "Bearer valid"})
    second_response = client.get("/api/v1/users/me", headers={"Authorization": "Bearer valid"})

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    first_user = first_response.json()["data"]
    second_user = second_response.json()["data"]
    assert first_user["id"] == second_user["id"]
    assert first_user["email"] is None
    assert first_user["first_name"] == "Local"
    assert second_user["last_name"] == "Investigator"


def _rsa_key_pair() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem.decode("utf-8"), public_pem.decode("utf-8")


@pytest.mark.asyncio
async def test_auth_service_accepts_clerk_token_without_email_claim():
    private_key, public_key = _rsa_key_pair()
    token = jwt.encode(
        {
            "sub": "user_sub_only",
            "azp": "http://localhost:3000",
            "iat": int(datetime.now(UTC).timestamp()),
            "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "local"},
    )
    settings = Settings(
        _env_file=None,
        clerk_jwt_key=public_key,
        clerk_authorized_parties=["http://localhost:3000"],
    )

    claims = await AuthService(settings).verify_bearer_token(token)

    assert claims.clerk_user_id == "user_sub_only"
    assert claims.email is None


@pytest.mark.asyncio
async def test_auth_service_rejects_token_from_untrusted_authorized_party():
    private_key, public_key = _rsa_key_pair()
    token = jwt.encode(
        {
            "sub": "user_123",
            "azp": "https://unknown.example.com",
            "iat": int(datetime.now(UTC).timestamp()),
            "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "local"},
    )
    settings = Settings(
        _env_file=None,
        clerk_jwt_key=public_key,
        clerk_authorized_parties=["http://localhost:3000"],
    )

    with pytest.raises(ApiError) as exc_info:
        await AuthService(settings).verify_bearer_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "UNAUTHORIZED"


def test_clerk_claims_uses_sub_as_canonical_identifier_without_email():
    claims = ClerkClaims.from_payload({"sub": "user_canonical"})

    assert claims.clerk_user_id == "user_canonical"
    assert claims.email is None
