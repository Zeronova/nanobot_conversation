"""Config flow for Nanobot Conversation."""

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_API_KEY, CONF_LLM_HASS_API, CONF_PROMPT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm, selector
from homeassistant.helpers.httpx_client import get_async_client

from .const import (
    CONF_API_URL,
    CONF_MAX_TOKENS,
    CONF_MODEL,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    DEFAULT_API_URL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DOMAIN,
    LOGGER,
    MAX_TOKENS_UPPER_BOUND,
    RECOMMENDED_CONVERSATION_OPTIONS,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_URL, default=DEFAULT_API_URL): str,
        vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): str,
        vol.Optional(CONF_API_KEY, default=""): str,
    }
)


async def validate_api_url(
    hass: HomeAssistant, api_url: str, api_key: str
) -> dict[str, str]:
    """Validate the API URL by listing models."""
    import openai

    client = openai.AsyncOpenAI(
        base_url=f"{api_url.rstrip('/')}/v1",
        api_key=api_key or "nanobot",
        http_client=get_async_client(hass),
    )

    errors: dict[str, str] = {}

    try:
        async for _ in client.with_options(timeout=10.0).models.list():
            break
    except openai.OpenAIError as err:
        LOGGER.warning("Connection test failed: %s", err)
        errors["base"] = "cannot_connect"
    except Exception:
        LOGGER.exception("Unexpected error testing connection")
        errors["base"] = "unknown"

    return errors


class NanobotConversationConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nanobot Conversation."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = await validate_api_url(
            self.hass,
            user_input[CONF_API_URL],
            user_input.get(CONF_API_KEY, ""),
        )

        if errors:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
            )

        return self.async_create_entry(
            title="Nanobot",
            data={
                CONF_API_URL: user_input[CONF_API_URL],
                CONF_API_KEY: user_input.get(CONF_API_KEY, ""),
                CONF_MODEL: user_input.get(CONF_MODEL, DEFAULT_MODEL),
            },
        )

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> "NanobotOptionsFlow":
        """Create the options flow."""
        return NanobotOptionsFlow()


class NanobotOptionsFlow(OptionsFlow):
    """Handle options flow for Nanobot."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options or RECOMMENDED_CONVERSATION_OPTIONS

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_MODEL,
                    default=options.get(CONF_MODEL, DEFAULT_MODEL),
                ): str,
                vol.Optional(
                    CONF_LLM_HASS_API,
                    default=options.get(CONF_LLM_HASS_API, [llm.LLM_API_ASSIST]),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(
                                value=llm.LLM_API_ASSIST,
                                label="Home Assistant area",
                            ),
                        ],
                        custom_value=True,
                        multiple=True,
                    ),
                ),
                vol.Optional(
                    CONF_PROMPT,
                    default=options.get(
                        CONF_PROMPT, llm.DEFAULT_INSTRUCTIONS_PROMPT
                    ),
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        multiline=True,
                    ),
                ),
                vol.Optional(
                    CONF_MAX_TOKENS,
                    default=options.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=MAX_TOKENS_UPPER_BOUND,
                        mode="box",
                        step=1,
                    ),
                ),
                vol.Optional(
                    CONF_TEMPERATURE,
                    default=options.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=2,
                        step=0.05,
                        mode="slider",
                    ),
                ),
                vol.Optional(
                    CONF_TOP_P,
                    default=options.get(CONF_TOP_P, DEFAULT_TOP_P),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=1,
                        step=0.05,
                        mode="slider",
                    ),
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
