"""Runtime data and OpenAI client factory for Codex AI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, TypeVar

import openai

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.httpx_client import get_async_client

from .auth import CODEX_BACKEND_BASE_URL, CodexTokens, build_default_headers, refresh_tokens
from .const import CONF_TOKENS

_T = TypeVar("_T")


class CodexTokenManager:
    """Manage Codex OAuth tokens for one config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the token manager."""
        self.hass = hass
        self.entry = entry
        self.tokens = CodexTokens.from_storage_dict(entry.data[CONF_TOKENS])

    async def async_refresh(self) -> None:
        """Refresh tokens and persist them in the config entry."""
        self.tokens = await refresh_tokens(get_async_client(self.hass), self.tokens)
        data = {**self.entry.data, CONF_TOKENS: self.tokens.as_storage_dict()}
        self.hass.config_entries.async_update_entry(self.entry, data=data)

    async def async_get_client(self) -> openai.AsyncOpenAI:
        """Return an OpenAI SDK client configured for the Codex backend."""
        if self.tokens.needs_refresh():
            await self.async_refresh()
        return openai.AsyncOpenAI(
            api_key=self.tokens.access_token,
            base_url=CODEX_BACKEND_BASE_URL,
            default_headers=build_default_headers(self.tokens),
            http_client=get_async_client(self.hass),
        )

    async def async_call_with_refresh(
        self, func: Callable[[openai.AsyncOpenAI], Awaitable[_T]]
    ) -> _T:
        """Call the Codex backend and retry once after refreshing on auth failure."""
        client = await self.async_get_client()
        try:
            return await func(client)
        except openai.AuthenticationError:
            await self.async_refresh()
            return await func(await self.async_get_client())


@dataclass(slots=True)
class CodexRuntimeData:
    """Runtime data for Codex AI."""

    token_manager: CodexTokenManager


type CodexConfigEntry = ConfigEntry[CodexRuntimeData]


def get_runtime(entry: ConfigEntry) -> CodexRuntimeData:
    """Return typed runtime data."""
    return entry.runtime_data
