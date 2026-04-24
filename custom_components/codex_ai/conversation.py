"""Conversation support for Codex AI."""

from __future__ import annotations

from typing import Literal

from homeassistant.components import conversation
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_MODEL, CONF_REASONING_EFFORT, DEFAULT_MODEL, DEFAULT_REASONING_EFFORT, DOMAIN
from .runtime import CodexConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: CodexConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up conversation entities."""
    async_add_entities([CodexConversationEntity(config_entry)])


class CodexConversationEntity(
    conversation.ConversationEntity, conversation.AbstractConversationAgent
):
    """Codex conversation agent."""

    _attr_has_entity_name = True
    _attr_name = "Codex AI"

    def __init__(self, entry: CodexConfigEntry) -> None:
        """Initialize the entity."""
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_conversation"

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return supported languages."""
        return MATCH_ALL

    async def async_added_to_hass(self) -> None:
        """Register as a conversation agent."""
        await super().async_added_to_hass()
        conversation.async_set_agent(self.hass, self.entry, self)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister as a conversation agent."""
        conversation.async_unset_agent(self.hass, self.entry)
        await super().async_will_remove_from_hass()

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Process user input."""
        runtime = self.entry.runtime_data

        async def call(client):
            return await client.responses.create(
                model=self.entry.data.get(CONF_MODEL, DEFAULT_MODEL),
                input=user_input.text,
                reasoning={
                    "effort": self.entry.data.get(
                        CONF_REASONING_EFFORT, DEFAULT_REASONING_EFFORT
                    )
                },
            )

        response = await runtime.token_manager.async_call_with_refresh(call)
        text = response.output_text
        chat_log.async_add_assistant_content_without_tools(
            conversation.AssistantContent(agent_id=DOMAIN, content=text)
        )
        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(text)
        return conversation.ConversationResult(
            response=intent_response,
            conversation_id=chat_log.conversation_id,
        )
