"""Codex AI integration."""

from __future__ import annotations

from types import MappingProxyType

from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    DEFAULT_AI_TASK_NAME,
    DEFAULT_CONVERSATION_NAME,
    DEFAULT_STT_NAME,
    DEFAULT_TTS_NAME,
    SUBENTRY_AI_TASK,
    SUBENTRY_CONVERSATION,
    SUBENTRY_STT,
    SUBENTRY_TTS,
)
from .runtime import CodexConfigEntry, CodexRuntimeData, CodexTokenManager

PLATFORMS = (Platform.AI_TASK, Platform.CONVERSATION, Platform.STT, Platform.TTS)


def default_subentries() -> list[dict]:
    """Return default subentries created for a Codex AI account."""
    return [
        {
            "data": {},
            "subentry_type": SUBENTRY_CONVERSATION,
            "title": DEFAULT_CONVERSATION_NAME,
            "unique_id": None,
        },
        {
            "data": {},
            "subentry_type": SUBENTRY_AI_TASK,
            "title": DEFAULT_AI_TASK_NAME,
            "unique_id": None,
        },
        {
            "data": {},
            "subentry_type": SUBENTRY_STT,
            "title": DEFAULT_STT_NAME,
            "unique_id": None,
        },
        {
            "data": {},
            "subentry_type": SUBENTRY_TTS,
            "title": DEFAULT_TTS_NAME,
            "unique_id": None,
        },
    ]


def _ensure_default_subentries(hass: HomeAssistant, entry: CodexConfigEntry) -> None:
    """Add default subentries to entries created by earlier versions."""
    existing = {subentry.subentry_type for subentry in entry.subentries.values()}
    for subentry in default_subentries():
        if subentry["subentry_type"] in existing:
            continue
        hass.config_entries.async_add_subentry(
            entry,
            ConfigSubentry(
                data=MappingProxyType(subentry["data"]),
                subentry_type=subentry["subentry_type"],
                title=subentry["title"],
                unique_id=subentry["unique_id"],
            ),
        )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Codex AI."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: CodexConfigEntry) -> bool:
    """Set up Codex AI from a config entry."""
    _ensure_default_subentries(hass, entry)
    entry.runtime_data = CodexRuntimeData(CodexTokenManager(hass, entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CodexConfigEntry) -> bool:
    """Unload Codex AI."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
