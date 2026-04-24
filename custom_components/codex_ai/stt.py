"""Speech-to-text support for Codex AI."""

from __future__ import annotations

from collections.abc import AsyncIterable
import io
import logging
import wave

from openai import OpenAIError

from homeassistant.components import stt
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_STT_MODEL, DEFAULT_STT_MODEL
from .runtime import CodexConfigEntry

_LOGGER = logging.getLogger(__name__)

_LANGUAGES = [
    "af-ZA", "ar-SA", "hy-AM", "az-AZ", "be-BY", "bs-BA", "bg-BG", "ca-ES",
    "zh-CN", "hr-HR", "cs-CZ", "da-DK", "nl-NL", "en-US", "et-EE", "fi-FI",
    "fr-FR", "gl-ES", "de-DE", "el-GR", "he-IL", "hi-IN", "hu-HU", "is-IS",
    "id-ID", "it-IT", "ja-JP", "kn-IN", "kk-KZ", "ko-KR", "lv-LV", "lt-LT",
    "mk-MK", "ms-MY", "mr-IN", "mi-NZ", "ne-NP", "no-NO", "fa-IR", "pl-PL",
    "pt-PT", "ro-RO", "ru-RU", "sr-RS", "sk-SK", "sl-SI", "es-ES", "sw-KE",
    "sv-SE", "fil-PH", "ta-IN", "th-TH", "tr-TR", "uk-UA", "ur-PK", "vi-VN",
    "cy-GB",
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: CodexConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up STT entities."""
    async_add_entities([CodexSTTEntity(config_entry)])


class CodexSTTEntity(stt.SpeechToTextEntity):
    """Codex STT entity."""

    _attr_has_entity_name = True
    _attr_name = "Codex STT"

    def __init__(self, entry: CodexConfigEntry) -> None:
        """Initialize the entity."""
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_stt"

    @property
    def supported_languages(self) -> list[str]:
        """Return supported languages."""
        return _LANGUAGES

    @property
    def supported_formats(self) -> list[stt.AudioFormats]:
        """Return supported formats."""
        return [stt.AudioFormats.WAV, stt.AudioFormats.OGG]

    @property
    def supported_codecs(self) -> list[stt.AudioCodecs]:
        """Return supported codecs."""
        return [stt.AudioCodecs.PCM, stt.AudioCodecs.OPUS]

    @property
    def supported_bit_rates(self) -> list[stt.AudioBitRates]:
        """Return supported bit rates."""
        return [
            stt.AudioBitRates.BITRATE_8,
            stt.AudioBitRates.BITRATE_16,
            stt.AudioBitRates.BITRATE_24,
            stt.AudioBitRates.BITRATE_32,
        ]

    @property
    def supported_sample_rates(self) -> list[stt.AudioSampleRates]:
        """Return supported sample rates."""
        return [
            stt.AudioSampleRates.SAMPLERATE_8000,
            stt.AudioSampleRates.SAMPLERATE_11000,
            stt.AudioSampleRates.SAMPLERATE_16000,
            stt.AudioSampleRates.SAMPLERATE_18900,
            stt.AudioSampleRates.SAMPLERATE_22000,
            stt.AudioSampleRates.SAMPLERATE_32000,
            stt.AudioSampleRates.SAMPLERATE_37800,
            stt.AudioSampleRates.SAMPLERATE_44100,
            stt.AudioSampleRates.SAMPLERATE_48000,
        ]

    @property
    def supported_channels(self) -> list[stt.AudioChannels]:
        """Return supported channels."""
        return [stt.AudioChannels.CHANNEL_MONO, stt.AudioChannels.CHANNEL_STEREO]

    async def async_process_audio_stream(
        self, metadata: stt.SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> stt.SpeechResult:
        """Process audio stream."""
        audio_bytes = bytearray()
        async for chunk in stream:
            audio_bytes.extend(chunk)
        audio_data = bytes(audio_bytes)

        if metadata.format == stt.AudioFormats.WAV:
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wav_file:
                wav_file.setnchannels(metadata.channel.value)
                wav_file.setsampwidth(metadata.bit_rate.value // 8)
                wav_file.setframerate(metadata.sample_rate.value)
                wav_file.writeframes(audio_data)
            audio_data = wav_buffer.getvalue()

        async def call(client):
            return await client.audio.transcriptions.create(
                model=self.entry.data.get(CONF_STT_MODEL, DEFAULT_STT_MODEL),
                file=(f"audio.{metadata.format.value}", audio_data),
                response_format="json",
                language=metadata.language.split("-")[0],
            )

        try:
            response = await self.entry.runtime_data.token_manager.async_call_with_refresh(call)
        except OpenAIError:
            _LOGGER.exception("Error during Codex STT")
            return stt.SpeechResult(None, stt.SpeechResultState.ERROR)

        if response.text:
            return stt.SpeechResult(response.text, stt.SpeechResultState.SUCCESS)
        return stt.SpeechResult(None, stt.SpeechResultState.ERROR)
