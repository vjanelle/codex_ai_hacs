"""Base entity helpers for Codex AI."""

from __future__ import annotations

from homeassistant.config_entries import ConfigSubentry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import Entity

from .const import CONF_MODEL, DOMAIN
from .runtime import CodexConfigEntry


class CodexBaseEntity(Entity):
    """Base entity for Codex AI config subentries."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, entry: CodexConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize the entity."""
        self.entry = entry
        self.subentry = subentry
        self._attr_unique_id = subentry.subentry_id
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            manufacturer="OpenAI",
            model=entry.data.get(CONF_MODEL),
            entry_type=dr.DeviceEntryType.SERVICE,
        )
