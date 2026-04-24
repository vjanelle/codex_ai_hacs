"""Config flow for Codex AI."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .auth import (
    DeviceCode,
    exchange_code_for_tokens,
    poll_device_code,
    request_device_code,
)
from .const import (
    CONF_MODEL,
    CONF_REASONING_EFFORT,
    CONF_STT_MODEL,
    CONF_TOKENS,
    CONF_TTS_MODEL,
    CONF_TTS_SPEED,
    CONF_TTS_VOICE,
    DEFAULT_MODEL,
    DEFAULT_REASONING_EFFORT,
    DEFAULT_STT_MODEL,
    DEFAULT_TTS_MODEL,
    DEFAULT_TTS_SPEED,
    DEFAULT_TTS_VOICE,
    DOMAIN,
)


class CodexAIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Codex AI."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow state."""
        self._device_code: DeviceCode | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Start device auth."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

        errors: dict[str, str] = {}
        try:
            self._device_code = await request_device_code(get_async_client(self.hass))
        except Exception:
            errors["base"] = "cannot_connect"

        if errors:
            return self.async_show_form(
                step_id="user", data_schema=vol.Schema({}), errors=errors
            )

        return await self.async_step_device()

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Wait for device auth completion."""
        if self._device_code is None:
            return await self.async_step_user({})

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                authorization = await poll_device_code(
                    get_async_client(self.hass), self._device_code
                )
                if authorization is None:
                    errors["base"] = "authorization_pending"
                else:
                    tokens = await exchange_code_for_tokens(
                        get_async_client(self.hass), authorization
                    )
                    await self.async_set_unique_id(tokens.account_id)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title="Codex AI",
                        data={
                            CONF_TOKENS: tokens.as_storage_dict(),
                            CONF_MODEL: DEFAULT_MODEL,
                            CONF_REASONING_EFFORT: DEFAULT_REASONING_EFFORT,
                            CONF_STT_MODEL: DEFAULT_STT_MODEL,
                            CONF_TTS_MODEL: DEFAULT_TTS_MODEL,
                            CONF_TTS_VOICE: DEFAULT_TTS_VOICE,
                            CONF_TTS_SPEED: DEFAULT_TTS_SPEED,
                        },
                    )
            except Exception:
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={
                "verification_url": self._device_code.verification_url,
                "user_code": self._device_code.user_code,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create options flow."""
        return CodexAIOptionsFlow(config_entry)


class CodexAIOptionsFlow(config_entries.OptionsFlow):
    """Options flow for Codex AI."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage options."""
        if user_input is not None:
            data = {**self.entry.data, **user_input}
            self.hass.config_entries.async_update_entry(self.entry, data=data)
            return self.async_create_entry(title="", data={})

        data = self.entry.data
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MODEL, default=data.get(CONF_MODEL, DEFAULT_MODEL)): str,
                    vol.Required(
                        CONF_REASONING_EFFORT,
                        default=data.get(CONF_REASONING_EFFORT, DEFAULT_REASONING_EFFORT),
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=["minimal", "low", "medium", "high"],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(
                        CONF_STT_MODEL, default=data.get(CONF_STT_MODEL, DEFAULT_STT_MODEL)
                    ): str,
                    vol.Required(
                        CONF_TTS_MODEL, default=data.get(CONF_TTS_MODEL, DEFAULT_TTS_MODEL)
                    ): str,
                    vol.Required(
                        CONF_TTS_VOICE, default=data.get(CONF_TTS_VOICE, DEFAULT_TTS_VOICE)
                    ): TextSelector(),
                    vol.Required(
                        CONF_TTS_SPEED, default=data.get(CONF_TTS_SPEED, DEFAULT_TTS_SPEED)
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=0.25,
                            max=4.0,
                            step=0.05,
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )
