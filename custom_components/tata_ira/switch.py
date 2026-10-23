"""Turn the cabin air conditioner on or off."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, UpdateFailed

from .const import CONF_VEHICLE_ID, DOMAIN
from .coordinator import IraCoordinator
from .device import vehicle_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add the air conditioning switch."""
    coordinator: IraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AirConditioningSwitch(coordinator, entry)])


class AirConditioningSwitch(CoordinatorEntity[IraCoordinator], SwitchEntity):
    """On starts the air conditioner for the saved duration. Off stops it."""

    _attr_has_entity_name = True
    _attr_name = "Air conditioning"
    _attr_icon = "mdi:air-conditioner"

    def __init__(self, coordinator: IraCoordinator, entry: ConfigEntry) -> None:
        """Identify the air conditioning switch."""
        super().__init__(coordinator)
        vehicle_id = entry.data[CONF_VEHICLE_ID]
        self._attr_unique_id = f"{vehicle_id}_ac"
        self._attr_device_info = vehicle_device_info(entry)

    @property
    def is_on(self) -> bool | None:
        """True while the car reports the air conditioner is running."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.ac_on

    async def async_turn_on(self, **kwargs: object) -> None:
        """Start the air conditioner for the duration set on the number entity."""
        await self._async_set(True)

    async def async_turn_off(self, **kwargs: object) -> None:
        """Stop the air conditioner."""
        await self._async_set(False)

    async def _async_set(self, on: bool) -> None:
        try:
            await self.coordinator.async_set_air_conditioning(on)
        except UpdateFailed as err:
            raise HomeAssistantError(str(err)) from err
