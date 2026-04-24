"""AI Task support for Codex AI."""

from __future__ import annotations

import base64
from json import JSONDecodeError
import logging
from typing import Any

from openai.types.responses import EasyInputMessageParam, ResponseInputParam
from voluptuous_openapi import convert

from homeassistant.components import ai_task, conversation
from homeassistant.config_entries import ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util.json import json_loads

from .auth import is_supported_image_mime
from .const import (
    CONF_MODEL,
    CONF_REASONING_EFFORT,
    DEFAULT_MODEL,
    DEFAULT_REASONING_EFFORT,
    SUBENTRY_AI_TASK,
)
from .entity import CodexBaseEntity
from .runtime import CodexConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: CodexConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AI Task entities."""
    entities = [
        CodexAITaskEntity(config_entry, subentry)
        for subentry in config_entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_AI_TASK
    ]
    for entity in entities:
        async_add_entities([entity], config_subentry_id=entity.subentry.subentry_id)


def _format_structure_schema(task: ai_task.GenDataTask) -> dict[str, Any] | None:
    """Format a Home Assistant AI task structure for Responses API."""
    if task.structure is None:
        return None
    return {
        "format": {
            "type": "json_schema",
            "name": task.name,
            "schema": convert(task.structure),
            "strict": False,
        }
    }


def _build_input(task: ai_task.GenDataTask) -> ResponseInputParam:
    """Build Responses API input from an AI task."""
    content: list[dict[str, Any]] = [{"type": "input_text", "text": task.instructions}]
    for attachment in task.attachments or []:
        if not is_supported_image_mime(attachment.mime_type):
            raise HomeAssistantError(
                f"Unsupported attachment MIME type for Codex AI: {attachment.mime_type}"
            )
        data = base64.b64encode(attachment.path.read_bytes()).decode()
        content.append(
            {
                "type": "input_image",
                "image_url": f"data:{attachment.mime_type};base64,{data}",
            }
        )
    return [EasyInputMessageParam(type="message", role="user", content=content)]


class CodexAITaskEntity(ai_task.AITaskEntity, CodexBaseEntity):
    """Codex AI Task entity."""

    _attr_supported_features = (
        ai_task.AITaskEntityFeature.GENERATE_DATA
        | ai_task.AITaskEntityFeature.SUPPORT_ATTACHMENTS
    )

    def __init__(self, entry: CodexConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize the entity."""
        CodexBaseEntity.__init__(self, entry, subentry)

    async def _async_generate_data(
        self,
        task: ai_task.GenDataTask,
        chat_log: conversation.ChatLog,
    ) -> ai_task.GenDataTaskResult:
        """Handle a generate data task."""
        runtime = self.entry.runtime_data
        text_format = _format_structure_schema(task)

        async def call(client):
            kwargs = {
                "model": self.entry.data.get(CONF_MODEL, DEFAULT_MODEL),
                "input": _build_input(task),
                "reasoning": {
                    "effort": self.entry.data.get(
                        CONF_REASONING_EFFORT, DEFAULT_REASONING_EFFORT
                    )
                },
            }
            if text_format is not None:
                kwargs["text"] = text_format
            return await client.responses.create(**kwargs)

        response = await runtime.token_manager.async_call_with_refresh(call)
        text = response.output_text

        if task.structure is None:
            return ai_task.GenDataTaskResult(
                conversation_id=chat_log.conversation_id,
                data=text,
            )
        try:
            data = json_loads(text)
        except JSONDecodeError as err:
            _LOGGER.error("Failed to parse Codex structured response: %s", text)
            raise HomeAssistantError("Error with Codex AI structured response") from err
        return ai_task.GenDataTaskResult(
            conversation_id=chat_log.conversation_id,
            data=data,
        )
