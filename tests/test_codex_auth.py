"""Tests for Codex AI auth helpers."""

from __future__ import annotations

import base64
import json
import pathlib
import sys
import unittest

sys.path.insert(
    0,
    str(
        pathlib.Path(__file__).resolve().parents[1]
        / "custom_components"
        / "codex_ai"
    ),
)

import auth  # noqa: E402


def jwt_with_payload(payload: dict) -> str:
    """Build an unsigned JWT-like token for parsing tests."""
    header = {"alg": "none", "typ": "JWT"}
    parts = []
    for item in (header, payload, b""):
        raw = item if isinstance(item, bytes) else json.dumps(item).encode()
        parts.append(base64.urlsafe_b64encode(raw).rstrip(b"=").decode())
    return ".".join(parts)


class TestCodexAuthHelpers(unittest.TestCase):
    """Test pure auth behavior."""

    def test_extracts_account_and_expiry_from_id_token(self) -> None:
        """JWT claims provide account id and expiry."""
        token = jwt_with_payload(
            {
                "chatgpt_account_id": "account-123",
                "exp": 1_800_000_000,
                "email": "user@example.com",
            }
        )

        claims = auth.decode_jwt_payload(token)

        self.assertEqual(claims["chatgpt_account_id"], "account-123")
        self.assertEqual(claims["exp"], 1_800_000_000)

    def test_builds_openai_client_headers_with_account_id(self) -> None:
        """Codex client headers include ChatGPT account routing."""
        tokens = auth.CodexTokens(
            id_token=jwt_with_payload({"chatgpt_account_id": "account-123"}),
            access_token="access-token",
            refresh_token="refresh-token",
            account_id="account-123",
            expires_at=1_800_000_000,
        )

        headers = auth.build_default_headers(tokens)

        self.assertEqual(headers["ChatGPT-Account-ID"], "account-123")
        self.assertEqual(headers["originator"], "codex_cli_rs")

    def test_non_image_attachment_is_rejected(self) -> None:
        """Only image attachments are valid for Codex AI tasks."""
        self.assertFalse(auth.is_supported_image_mime("audio/wav"))
        self.assertTrue(auth.is_supported_image_mime("image/png"))


if __name__ == "__main__":
    unittest.main()
