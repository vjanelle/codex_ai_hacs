"""Constants for Codex AI."""

from __future__ import annotations

from logging import getLogger

DOMAIN = "codex_ai"
LOGGER = getLogger(__package__)

CONF_MODEL = "model"
CONF_REASONING_EFFORT = "reasoning_effort"
CONF_STT_MODEL = "stt_model"
CONF_TTS_MODEL = "tts_model"
CONF_TTS_VOICE = "tts_voice"
CONF_TTS_SPEED = "tts_speed"
CONF_TOKENS = "tokens"

DEFAULT_MODEL = "gpt-5.5"
DEFAULT_REASONING_EFFORT = "medium"
DEFAULT_STT_MODEL = "gpt-4o-mini-transcribe"
DEFAULT_TTS_MODEL = "gpt-4o-mini-tts"
DEFAULT_TTS_VOICE = "marin"
DEFAULT_TTS_SPEED = 1.0
