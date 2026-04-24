"""Text-to-speech support for Codex AI."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
import logging

from openai import OpenAIError
from propcache.api import cached_property

from homeassistant.components.tts import (
    ATTR_PREFERRED_FORMAT,
    ATTR_VOICE,
    TextToSpeechEntity,
    TtsAudioType,
    Voice,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_TTS_MODEL,
    CONF_TTS_SPEED,
    CONF_TTS_VOICE,
    DEFAULT_TTS_MODEL,
    DEFAULT_TTS_SPEED,
    DEFAULT_TTS_VOICE,
)
from .runtime import CodexConfigEntry

_LOGGER = logging.getLogger(__name__)

_VOICES = [
    Voice(voice, voice.title())
    for voice in (
        "marin", "cedar", "alloy", "ash", "ballad", "coral", "echo", "fable",
        "nova", "onyx", "sage", "shimmer", "verse",
    )
]
_FORMATS = ["mp3", "opus", "aac", "flac", "wav", "pcm"]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: CodexConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up TTS entities."""
    async_add_entities([CodexTTSEntity(config_entry)])


class CodexTTSEntity(TextToSpeechEntity):
    """Codex TTS entity."""

    _attr_has_entity_name = True
    _attr_name = "Codex TTS"
    _attr_supported_options = [ATTR_VOICE, ATTR_PREFERRED_FORMAT]
    _attr_supported_languages = ["en-US"]
    _attr_default_language = "en-US"

    def __init__(self, entry: CodexConfigEntry) -> None:
        """Initialize the entity."""
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_tts"

    @callback
    def async_get_supported_voices(self, language: str) -> list[Voice]:
        """Return supported voices."""
        return _VOICES

    @cached_property
    def default_options(self) -> Mapping[str, Any]:
        """Return default TTS options."""
        return {
            ATTR_VOICE: self.entry.data.get(CONF_TTS_VOICE, DEFAULT_TTS_VOICE),
            ATTR_PREFERRED_FORMAT: "mp3",
        }

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> TtsAudioType:
        """Load TTS audio."""
        merged = {**self.default_options, **self.entry.data, **options}
        response_format = merged[ATTR_PREFERRED_FORMAT]
        if response_format == "ogg":
            response_format = "opus"
        elif response_format == "raw":
            response_format = "pcm"
        elif response_format not in _FORMATS:
            response_format = "mp3"

        async def call(client):
            async with client.audio.speech.with_streaming_response.create(
                model=merged.get(CONF_TTS_MODEL, DEFAULT_TTS_MODEL),
                voice=merged.get(ATTR_VOICE, DEFAULT_TTS_VOICE),
                input=message,
                speed=merged.get(CONF_TTS_SPEED, DEFAULT_TTS_SPEED),
                response_format=response_format,
            ) as response:
                data = bytearray()
                async for chunk in response.iter_bytes():
                    data.extend(chunk)
                return bytes(data)

        try:
            audio = await self.entry.runtime_data.token_manager.async_call_with_refresh(call)
        except OpenAIError as exc:
            _LOGGER.exception("Error during Codex TTS")
            raise HomeAssistantError(exc) from exc
        return response_format, audio
