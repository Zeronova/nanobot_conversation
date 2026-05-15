"""Conversation agent for Nanobot."""

from collections.abc import AsyncGenerator, Callable
import json
from typing import Any, Literal

import openai
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PROMPT, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, llm
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.json import json_dumps

from . import NanobotConfigEntry
from .const import (
    CONF_MAX_TOKENS,
    CONF_MODEL,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    DOMAIN,
    LOGGER,
)

MAX_TOOL_ITERATIONS = 10


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: NanobotConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Nanobot conversation entity."""
    async_add_entities([NanobotConversationEntity(config_entry)])


def _format_tool(
    tool: llm.Tool,
    custom_serializer: Callable[[Any], Any] | None,
) -> dict[str, Any]:
    """Format a tool specification for the OpenAI Chat Completions API."""
    from voluptuous_openapi import convert

    tool_spec = {
        "type": "function",
        "function": {
            "name": tool.name,
            "parameters": convert(tool.parameters, custom_serializer=custom_serializer),
        },
    }
    if tool.description:
        tool_spec["function"]["description"] = tool.description
    return tool_spec


def _chat_message_from_content(
    content: conversation.Content,
) -> ChatCompletionMessageParam | None:
    """Convert conversation content to OpenAI Chat Completions message format."""
    if isinstance(content, conversation.ToolResultContent):
        return ChatCompletionToolMessageParam(
            role="tool",
            tool_call_id=content.tool_call_id,
            content=json_dumps(content.tool_result),
        )

    if isinstance(content, conversation.SystemContent):
        return ChatCompletionSystemMessageParam(
            role="system", content=content.content
        )

    if isinstance(content, conversation.UserContent):
        return ChatCompletionUserMessageParam(
            role="user", content=content.content
        )

    if isinstance(content, conversation.AssistantContent):
        param = ChatCompletionAssistantMessageParam(
            role="assistant",
            content=content.content,
        )
        if content.tool_calls:
            param["tool_calls"] = [
                {
                    "type": "function",
                    "id": tc.id,
                    "function": {
                        "arguments": json_dumps(tc.tool_args),
                        "name": tc.tool_name,
                    },
                }
                for tc in content.tool_calls
            ]
        return param

    LOGGER.warning("Could not convert message content: %s", type(content).__name__)
    return None


def _decode_tool_arguments(arguments: str) -> Any:
    """Decode tool call arguments from JSON."""
    try:
        return json.loads(arguments)
    except json.JSONDecodeError as err:
        raise HomeAssistantError(f"Invalid tool argument JSON: {err}") from err


class NanobotConversationEntity(conversation.ConversationEntity):
    """Conversation entity that talks to the nanobot API."""

    _attr_has_entity_name = True
    _attr_supported_features = conversation.ConversationEntityFeature.CONTROL

    def __init__(self, entry: NanobotConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__()
        self.entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Nanobot",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return supported languages."""
        return MATCH_ALL

    async def async_added_to_hass(self) -> None:
        """When entity is added to Home Assistant."""
        await super().async_added_to_hass()
        conversation.async_set_agent(self.hass, self.entry, self)

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from Home Assistant."""
        conversation.async_unset_agent(self.hass, self.entry)
        await super().async_will_remove_from_hass()

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Process the user input and call the nanobot API."""

        # --- Step 1: Provide LLM context (system prompt + tools) ---
        options = self.entry.options
        try:
            await chat_log.async_provide_llm_data(
                llm_context=user_input.as_llm_context(DOMAIN),
                user_llm_prompt=options.get(CONF_PROMPT),
                user_extra_system_prompt=user_input.extra_system_prompt,
            )
        except conversation.ConverseError as err:
            return err.as_conversation_result()

        # --- Step 2: Prepare the OpenAI client and session ---
        client = self.entry.runtime_data
        options = self.entry.options
        model = options.get(CONF_MODEL) or None
        conversation_id = user_input.conversation_id or user_input.agent_id

        # --- Step 3: Build single user message ---
        # nanobot serve only accepts a single user message (no system/assistant/tool roles)
        system_parts: list[str] = []
        user_parts: list[str] = []
        for content in chat_log.content:
            if isinstance(content, conversation.SystemContent):
                system_parts.append(content.content)
            elif isinstance(content, conversation.UserContent):
                user_parts.append(content.content)

        combined = ""
        if system_parts:
            combined = "\n\n".join(system_parts) + "\n\n"
        combined += "Keine Emojis oder Smileys verwenden.\n"
        combined += "Beziehe dich in deiner Antwort auf den nachfolgenden Benutzertext, nicht auf den Systemteil oben.\n"
        combined += "Antworte auf Deutsch. Verwende deutsche Umlaute (ä, ö, ü, ß) korrekt.\n\n"
        combined += "\n\n".join(user_parts)

        messages: list[ChatCompletionMessageParam] = [
            {"role": "user", "content": combined}
        ]

        # Build tools from llm_api
        tools: list[dict[str, Any]] | None = None
        if chat_log.llm_api and chat_log.llm_api.tools:
            tools = [
                _format_tool(t, chat_log.llm_api.custom_serializer)
                for t in chat_log.llm_api.tools
            ]

        # --- Step 4: Tool-calling loop ---
        for _iteration in range(MAX_TOOL_ITERATIONS):
            # Make the API call
            api_kwargs: dict[str, Any] = {
                "model": model or None,
                "messages": messages,
                "extra_body": {
                    "session_id": f"ha_{conversation_id}_{self.entry.entry_id}",
                },
            }
            if max_tokens := options.get(CONF_MAX_TOKENS):
                api_kwargs["max_tokens"] = max_tokens
            if temperature := options.get(CONF_TEMPERATURE):
                api_kwargs["temperature"] = temperature
            if top_p := options.get(CONF_TOP_P):
                api_kwargs["top_p"] = top_p
            if tools:
                api_kwargs["tools"] = tools
            try:
                result = await client.chat.completions.create(**api_kwargs)
            except openai.OpenAIError as err:
                LOGGER.error("API error: %s", err)
                raise HomeAssistantError(
                    f"Error talking to nanobot: {err}"
                ) from err

            if not result.choices:
                LOGGER.error("API returned empty choices")
                raise HomeAssistantError("API returned empty response")

            msg = result.choices[0].message

            # Build the delta dict for the chat_log stream
            delta: conversation.AssistantContentDeltaDict = {
                "role": "assistant",
                "content": msg.content or "",
            }

            if msg.tool_calls:
                delta["tool_calls"] = [
                    llm.ToolInput(
                        id=tc.id,
                        tool_name=tc.function.name,
                        tool_args=_decode_tool_arguments(tc.function.arguments),
                    )
                    for tc in msg.tool_calls
                    if tc.type == "function"
                ]

            # Feed into chat_log — this executes tool calls automatically
            async for _ in chat_log.async_add_delta_content_stream(
                self.entity_id,
                _single_delta_stream(delta),
            ):
                pass

            # Check if there are tool results pending — if not, we're done
            if not chat_log.unresponded_tool_results:
                break

            # Build a follow-up single user message with tool results
            # (nanobot serve can't handle multiple messages with tool roles)
            tool_summaries: list[str] = []
            for unresponded in chat_log.unresponded_tool_results:
                result_text = json_dumps(unresponded.tool_result)
                tool_summaries.append(
                    f"Tool result ({unresponded.tool_call_id}): {result_text}"
                )

            follow_up = (
                f"{combined}\n\n"
                f"Assistant called the following tools:\n"
                f"{chr(10).join(tool_summaries)}\n\n"
                f"Given the tool results above, provide your final response to the user in German."
                f" Verwende deutsche Umlaute (ä, ö, ü, ß) korrekt."
                f" Keine Emojis oder Smileys verwenden."
            )
            messages = [{"role": "user", "content": follow_up}]

        # --- Step 5: Return the result ---
        return conversation.async_get_result_from_chat_log(user_input, chat_log)


async def _single_delta_stream(
    delta: conversation.AssistantContentDeltaDict,
) -> AsyncGenerator[conversation.AssistantContentDeltaDict]:
    """Yield a single assistant content delta dict.

    Wraps a single message in the async generator format expected
    by chat_log.async_add_delta_content_stream().
    """
    yield delta
