"""Battery percentage and remaining charge time."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
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
    """Add the battery and charge-time sensors."""
    coordinator: IraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            BatterySensor(coordinator, entry),
            ChargeTimeSensor(coordinator, entry),
        ]
    )


class IraSensor(CoordinatorEntity[IraCoordinator], SensorEntity):
    """A reading from the car."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: IraCoordinator, entry: ConfigEntry) -> None:
        """Attach this sensor to the car."""
        super().__init__(coordinator)
        self._attr_device_info = vehicle_device_info(entry)
        self._vehicle_id = entry.data[CONF_VEHICLE_ID]


class BatterySensor(IraSensor):
    """High-voltage battery state of charge."""

    _attr_name = "Battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator: IraCoordinator, entry: ConfigEntry) -> None:
        """Identify the battery sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._vehicle_id}_battery"

    @property
    def native_value(self) -> float | None:
        """Battery percentage."""
        return self.coordinator.data.battery_percent


class ChargeTimeSensor(IraSensor):
    """Minutes until the current charge session finishes."""

    _attr_name = "Charge time remaining"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(self, coordinator: IraCoordinator, entry: ConfigEntry) -> None:
        """Identify the charge-time sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._vehicle_id}_charge_time"

    @property
    def native_value(self) -> int | None:
        """Minutes remaining while the car is charging."""
        return self.coordinator.data.charge_minutes_remaining

    @property
    def available(self) -> bool:
        """Hide the timer when the car is not charging."""
        return (
            super().available
            and self.coordinator.data.charge_minutes_remaining is not None
        )
