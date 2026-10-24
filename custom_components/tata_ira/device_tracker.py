"""Where the car last reported it is."""

from __future__ import annotations

from homeassistant.components.device_tracker import SourceType, TrackerEntity
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
    """Add the car's location."""
    coordinator: IraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CarTracker(coordinator, entry)])


class CarTracker(CoordinatorEntity[IraCoordinator], TrackerEntity):
    """The position from the car's last vehicle-state reading."""

    _attr_has_entity_name = True
    _attr_name = "Location"
    _attr_source_type = SourceType.GPS

    def __init__(self, coordinator: IraCoordinator, entry: ConfigEntry) -> None:
        """Identify the location tracker."""
        super().__init__(coordinator)
        vehicle_id = entry.data[CONF_VEHICLE_ID]
        self._attr_unique_id = f"{vehicle_id}_location"
        self._attr_device_info = vehicle_device_info(entry)

    @property
    def available(self) -> bool:
        """Available once the car has reported a position."""
        return super().available and self.latitude is not None and self.longitude is not None

    @property
    def latitude(self) -> float | None:
        """Last reported latitude."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.latitude

    @property
    def longitude(self) -> float | None:
        """Last reported longitude."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.longitude
