"""Codex ChatGPT OAuth helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import base64
import json
from typing import Any

CODEX_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
CODEX_ISSUER = "https://auth.openai.com"
CODEX_BACKEND_BASE_URL = "https://chatgpt.com/backend-api/codex"
CODEX_ORIGINATOR = "codex_cli_rs"
TOKEN_REFRESH_SKEW = timedelta(minutes=5)


@dataclass(slots=True)
class DeviceCode:
    """Device auth data shown to the user."""

    verification_url: str
    user_code: str
    device_auth_id: str
    interval: int


@dataclass(slots=True)
class CodexTokens:
    """Tokens needed to call the Codex backend."""

    id_token: str
    access_token: str
    refresh_token: str
    account_id: str | None
    expires_at: int | None

    def needs_refresh(self) -> bool:
        """Return true if the token is near expiry."""
        if self.expires_at is None:
            return False
        refresh_at = datetime.fromtimestamp(self.expires_at, UTC) - TOKEN_REFRESH_SKEW
        return datetime.now(UTC) >= refresh_at

    def as_storage_dict(self) -> dict[str, Any]:
        """Serialize tokens for a Home Assistant config entry."""
        return {
            "id_token": self.id_token,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "account_id": self.account_id,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_storage_dict(cls, data: dict[str, Any]) -> "CodexTokens":
        """Load tokens from a Home Assistant config entry."""
        return cls(
            id_token=data["id_token"],
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            account_id=data.get("account_id"),
            expires_at=data.get("expires_at"),
        )


def decode_jwt_payload(token: str) -> dict[str, Any]:
    """Decode JWT payload without verifying signature."""
    try:
        payload = token.split(".")[1]
    except IndexError as err:
        raise ValueError("Invalid JWT") from err
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


def tokens_from_response(data: dict[str, Any]) -> CodexTokens:
    """Create Codex tokens from OAuth token endpoint response."""
    id_token = data["id_token"]
    claims = decode_jwt_payload(id_token)
    return CodexTokens(
        id_token=id_token,
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        account_id=claims.get("chatgpt_account_id"),
        expires_at=claims.get("exp"),
    )


def build_default_headers(tokens: CodexTokens) -> dict[str, str]:
    """Return headers used by Codex for ChatGPT backend routing."""
    headers = {"originator": CODEX_ORIGINATOR}
    if tokens.account_id:
        headers["ChatGPT-Account-ID"] = tokens.account_id
    return headers


def is_supported_image_mime(mime_type: str | None) -> bool:
    """Return true if the MIME type is a supported image input."""
    return bool(mime_type and mime_type.startswith("image/"))


async def request_device_code(http_client: Any) -> DeviceCode:
    """Start Codex device auth."""
    response = await http_client.post(
        f"{CODEX_ISSUER}/api/accounts/deviceauth/usercode",
        json={"client_id": CODEX_CLIENT_ID},
    )
    response.raise_for_status()
    data = response.json()
    return DeviceCode(
        verification_url=f"{CODEX_ISSUER}/codex/device",
        user_code=data.get("user_code") or data["usercode"],
        device_auth_id=data["device_auth_id"],
        interval=int(data.get("interval", 5)),
    )


async def poll_device_code(http_client: Any, device_code: DeviceCode) -> dict[str, str] | None:
    """Poll device auth once; return authorization data when ready."""
    response = await http_client.post(
        f"{CODEX_ISSUER}/api/accounts/deviceauth/token",
        json={
            "device_auth_id": device_code.device_auth_id,
            "user_code": device_code.user_code,
        },
    )
    if response.status_code in (403, 404):
        return None
    response.raise_for_status()
    return response.json()


async def exchange_code_for_tokens(
    http_client: Any, authorization: dict[str, str]
) -> CodexTokens:
    """Exchange device authorization code for tokens."""
    response = await http_client.post(
        f"{CODEX_ISSUER}/oauth/token",
        data={
            "grant_type": "authorization_code",
            "code": authorization["authorization_code"],
            "redirect_uri": f"{CODEX_ISSUER}/deviceauth/callback",
            "client_id": CODEX_CLIENT_ID,
            "code_verifier": authorization["code_verifier"],
        },
    )
    response.raise_for_status()
    return tokens_from_response(response.json())


async def refresh_tokens(http_client: Any, tokens: CodexTokens) -> CodexTokens:
    """Refresh Codex OAuth tokens."""
    response = await http_client.post(
        f"{CODEX_ISSUER}/oauth/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": tokens.refresh_token,
            "client_id": CODEX_CLIENT_ID,
        },
    )
    response.raise_for_status()
    return tokens_from_response(response.json())
