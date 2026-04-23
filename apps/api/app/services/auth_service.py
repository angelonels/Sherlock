from typing import Any

import httpx
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.core.config import Settings
from app.core.errors import ApiError
from app.schemas.auth import ClerkClaims


class AuthService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def verify_credentials(
        self,
        credentials: HTTPAuthorizationCredentials | None,
    ) -> ClerkClaims:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise ApiError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="UNAUTHORIZED",
                message="Missing bearer token.",
            )

        return await self.verify_bearer_token(credentials.credentials)

    async def verify_bearer_token(self, token: str) -> ClerkClaims:
        key = await self._verification_key(token)
        if not key:
            raise ApiError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="UNAUTHORIZED",
                message="Clerk JWT verification is not configured.",
            )

        try:
            issuer = self.settings.effective_clerk_issuer_url
            decode_options = {
                "verify_aud": bool(self.settings.clerk_audience),
                "verify_iss": bool(issuer),
            }
            decode_kwargs: dict[str, Any] = {
                "algorithms": ["RS256"],
                "options": decode_options,
            }
            if self.settings.clerk_audience:
                decode_kwargs["audience"] = self.settings.clerk_audience
            if issuer:
                decode_kwargs["issuer"] = issuer

            payload = jwt.decode(
                token,
                key,
                **decode_kwargs,
            )
            if not payload.get("sub"):
                raise ValueError("Clerk token is missing a subject.")
            self._verify_authorized_party(payload)
            return ClerkClaims.from_payload(payload)
        except (JWTError, KeyError, ValueError) as exc:
            raise ApiError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="UNAUTHORIZED",
                message="Invalid bearer token.",
            ) from exc

    async def _verification_key(self, token: str) -> dict[str, Any] | str | None:
        if self.settings.normalized_clerk_jwt_key:
            return self.settings.normalized_clerk_jwt_key

        jwks_url = self._jwks_url()
        if not jwks_url:
            return None

        try:
            header = jwt.get_unverified_header(token)
            jwks = await self._fetch_jwks(jwks_url)
            return self._select_jwk(jwks, header.get("kid"))
        except (JWTError, httpx.HTTPError, KeyError) as exc:
            raise ApiError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="UNAUTHORIZED",
                message="Invalid bearer token.",
            ) from exc

    def _jwks_url(self) -> str | None:
        if self.settings.clerk_jwks_url:
            return str(self.settings.clerk_jwks_url)
        issuer = self.settings.effective_clerk_issuer_url
        if issuer:
            return f"{issuer.rstrip('/')}/.well-known/jwks.json"
        return None

    async def _fetch_jwks(self, jwks_url: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _select_jwk(jwks: dict[str, Any], kid: str | None) -> dict[str, Any]:
        keys = jwks.get("keys", [])
        for key in keys:
            if key.get("kid") == kid:
                return key
        raise KeyError("No matching Clerk signing key found.")

    def _verify_authorized_party(self, payload: dict[str, Any]) -> None:
        if not self.settings.clerk_authorized_parties:
            return
        authorized_party = payload.get("azp")
        if authorized_party not in self.settings.clerk_authorized_parties:
            raise ValueError("Token authorized party is not allowed.")
