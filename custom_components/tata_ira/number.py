"""How long the next air-conditioning start should run."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode, RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_VEHICLE_ID, DOMAIN
from .coordinator import IraCoordinator
from .device import vehicle_device_info
from .parser import AC_MINUTES_MAX, AC_MINUTES_MIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add the air conditioning duration control."""
    coordinator: IraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AirConditioningDuration(coordinator, entry)])


class AirConditioningDuration(RestoreNumber, NumberEntity):
    """Minutes used the next time the air conditioner is turned on."""

    _attr_has_entity_name = True
    _attr_name = "Air conditioning duration"
    _attr_icon = "mdi:timer-outline"
    _attr_native_min_value = AC_MINUTES_MIN
    _attr_native_max_value = AC_MINUTES_MAX
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(self, coordinator: IraCoordinator, entry: ConfigEntry) -> None:
        """Identify the duration control."""
        self.coordinator = coordinator
        vehicle_id = entry.data[CONF_VEHICLE_ID]
        self._attr_unique_id = f"{vehicle_id}_ac_minutes"
        self._attr_device_info = vehicle_device_info(entry)
        self._attr_native_value = float(coordinator.ac_minutes)

    async def async_added_to_hass(self) -> None:
        """Restore the last duration the user chose."""
        await super().async_added_to_hass()
        restored = await self.async_get_last_number_data()
        if restored is not None and restored.native_value is not None:
            self._attr_native_value = restored.native_value
            self.coordinator.ac_minutes = int(restored.native_value)

    async def async_set_native_value(self, value: float) -> None:
        """Remember the duration. The car is not contacted until the switch turns on."""
        minutes = int(value)
        self._attr_native_value = float(minutes)
        self.coordinator.ac_minutes = minutes
        self.async_write_ha_state()
