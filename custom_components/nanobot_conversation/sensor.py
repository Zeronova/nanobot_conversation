"""Sensor platform for the Nanobot Conversation integration.

Provides sensors that expose status and usage data from the nanobot serve API.
"""

from datetime import timedelta
import logging

import aiohttp

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from . import NanobotConfigEntry
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: NanobotConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Nanobot sensor entities."""
    data = config_entry.runtime_data

    # Health check coordinator
    coordinator = NanobotHealthCoordinator(hass, data)
    await coordinator.async_config_entry_first_refresh()

    sensors: list[SensorEntity] = [
        NanobotModelSensor(config_entry),
        NanobotStatusSensor(coordinator, config_entry),
        NanobotTokenSensor(config_entry),
        NanobotLatencySensor(config_entry),
        NanobotTotalRequestsSensor(config_entry),
        NanobotMonthlyTokensSensor(config_entry),
        NanobotLastInteractionSensor(config_entry),
        NanobotAvailableModelsSensor(config_entry),
    ]

    data._sensor_entities = sensors
    async_add_entities(sensors)


class NanobotHealthCoordinator(DataUpdateCoordinator[str]):
    """Coordinator for polling the nanobot /health endpoint."""

    def __init__(self, hass: HomeAssistant, data) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Nanobot Health",
            update_interval=SCAN_INTERVAL,
        )
        self._data = data
        self._api_url = data.api_url

    async def _async_update_data(self) -> str:
        """Fetch the health status."""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self._api_url}/health") as resp:
                    if resp.status == 200:
                        self._data.status = "online"
                        return "online"
                    self._data.status = "offline"
                    return "offline"
        except (aiohttp.ClientError, TimeoutError) as err:
            self._data.status = "offline"
            raise UpdateFailed(f"Health check failed: {err}") from err


class NanobotModelSensor(SensorEntity):
    """The current model in use by the nanobot API."""

    _attr_has_entity_name = True
    _attr_name = "Modell"
    _attr_icon = "mdi:chip"

    def __init__(self, entry: NanobotConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__()
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_model"
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Nanobot",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> str:
        """Return the model name."""
        return self._entry.runtime_data.model


class NanobotStatusSensor(CoordinatorEntity, SensorEntity):
    """API reachability status."""

    _attr_has_entity_name = True
    _attr_name = "Status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["online", "offline", "unknown"]

    def __init__(
        self, coordinator: NanobotHealthCoordinator, entry: NanobotConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Nanobot",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> str:
        """Return the status."""
        return self._entry.runtime_data.status

    @property
    def icon(self) -> str:
        """Return an icon based on status."""
        return {
            "online": "mdi:cloud-check",
            "offline": "mdi:cloud-alert",
            "unknown": "mdi:cloud-question",
        }.get(self._entry.runtime_data.status, "mdi:cloud-question")


class NanobotTokenSensor(SensorEntity):
    """Daily token usage counter."""

    _attr_has_entity_name = True
    _attr_name = "Tägliche Tokens"
    _attr_icon = "mdi:counter"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, entry: NanobotConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__()
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_daily_tokens"
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Nanobot",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> int:
        """Return the accumulated token count."""
        return self._entry.runtime_data.daily_tokens

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit."""
        return "Tokens"


class NanobotLatencySensor(SensorEntity):
    """Last API response latency."""

    _attr_has_entity_name = True
    _attr_name = "Antwortzeit"
    _attr_icon = "mdi:timer-outline"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: NanobotConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__()
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_latency"
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Nanobot",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> float | None:
        """Return the last latency in milliseconds."""
        return self._entry.runtime_data.last_latency or None

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit."""
        return "ms"


class NanobotTotalRequestsSensor(SensorEntity):
    """Total number of API requests made."""

    _attr_has_entity_name = True
    _attr_name = "Anfragen Gesamt"
    _attr_icon = "mdi:api"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, entry: NanobotConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__()
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_total_requests"
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Nanobot",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> int:
        """Return the total request count."""
        return self._entry.runtime_data.total_requests


class NanobotMonthlyTokensSensor(SensorEntity):
    """Monthly token usage counter."""

    _attr_has_entity_name = True
    _attr_name = "Monatliche Tokens"
    _attr_icon = "mdi:counter"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, entry: NanobotConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__()
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_monthly_tokens"
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Nanobot",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> int:
        """Return the monthly accumulated token count."""
        return self._entry.runtime_data.monthly_tokens

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit."""
        return "Tokens"


class NanobotLastInteractionSensor(SensorEntity):
    """Timestamp of the last conversation interaction."""

    _attr_has_entity_name = True
    _attr_name = "Letzte Interaktion"
    _attr_icon = "mdi:chat"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, entry: NanobotConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__()
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_last_interaction"
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Nanobot",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> str | None:
        """Return the last interaction timestamp."""
        return self._entry.runtime_data.last_interaction


class NanobotAvailableModelsSensor(SensorEntity):
    """List of available models from the API."""

    _attr_has_entity_name = True
    _attr_name = "Verfügbare Modelle"
    _attr_icon = "mdi:database"

    def __init__(self, entry: NanobotConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__()
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_available_models"
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Nanobot",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> str:
        """Return comma-separated available models."""
        models = self._entry.runtime_data.available_models or ["?"]
        return ", ".join(models)
