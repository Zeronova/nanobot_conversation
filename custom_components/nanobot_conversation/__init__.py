"""The Nanobot Conversation integration.

Connects Home Assistant to the nanobot OpenAI-compatible API
(http://localhost:8900/v1) for conversation processing with
full tool/function-calling support.
"""

from openai import AsyncOpenAI, OpenAIError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.httpx_client import get_async_client

from .const import CONF_API_URL, DEFAULT_API_URL, DOMAIN, LOGGER

PLATFORMS = [Platform.CONVERSATION]

type NanobotConfigEntry = ConfigEntry[AsyncOpenAI]


async def async_setup_entry(hass: HomeAssistant, entry: NanobotConfigEntry) -> bool:
    """Set up Nanobot Conversation from a config entry."""
    api_url = entry.data.get(CONF_API_URL, DEFAULT_API_URL)
    api_key = entry.data.get(CONF_API_KEY, "")

    client = AsyncOpenAI(
        base_url=f"{api_url.rstrip('/')}/v1",
        api_key=api_key or "nanobot",
        http_client=get_async_client(hass),
    )

    try:
        async for _ in client.with_options(timeout=10.0).models.list():
            break
    except OpenAIError as err:
        LOGGER.warning("Could not connect to nanobot API at %s: %s", api_url, err)
        raise ConfigEntryNotReady(
            f"Cannot reach nanobot API at {api_url}: {err}"
        ) from err

    entry.runtime_data = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(
    hass: HomeAssistant, entry: NanobotConfigEntry
) -> None:
    """Handle config entry update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: NanobotConfigEntry) -> bool:
    """Unload Nanobot Conversation."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
