"""Whether the car is charging."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_VEHICLE_ID, DOMAIN
from .coordinator import IraCoordinator
from .device import vehicle_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add the charging sensor."""
    coordinator: IraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ChargingSensor(coordinator, entry)])


class ChargingSensor(CoordinatorEntity[IraCoordinator], BinarySensorEntity):
    """On while the high-voltage battery is charging."""

    _attr_has_entity_name = True
    _attr_name = "Charging"
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def __init__(self, coordinator: IraCoordinator, entry: ConfigEntry) -> None:
        """Identify the charging sensor."""
        super().__init__(coordinator)
        vehicle_id = entry.data[CONF_VEHICLE_ID]
        self._attr_unique_id = f"{vehicle_id}_charging"
        self._attr_device_info = vehicle_device_info(entry)

    @property
    def is_on(self) -> bool | None:
        """True while the car reports it is charging."""
        return self.coordinator.data.charging
