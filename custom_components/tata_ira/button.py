"""Manual refresh of the car's status."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import CONF_VEHICLE_ID, DOMAIN
from .coordinator import IraCoordinator
from .device import vehicle_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add the refresh button."""
    coordinator: IraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RefreshButton(coordinator, entry)])


class RefreshButton(ButtonEntity):
    """Fetch battery, charging, air conditioning, and lock state from the car now."""

    _attr_has_entity_name = True
    _attr_name = "Refresh"
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: IraCoordinator, entry: ConfigEntry) -> None:
        """Identify the refresh button."""
        self.coordinator = coordinator
        vehicle_id = entry.data[CONF_VEHICLE_ID]
        self._attr_unique_id = f"{vehicle_id}_refresh"
        self._attr_device_info = vehicle_device_info(entry)

    async def async_press(self) -> None:
        """Read the car immediately, without waiting for the next poll."""
        try:
            await self.coordinator.async_refresh()
        except UpdateFailed as err:
            raise HomeAssistantError(str(err)) from err
