"""Battery percentage and remaining charge time."""

from __future__ import annotations

from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPressure, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
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
    _keep_tyre_pressure_in_psi(hass, entry)
    async_add_entities(
        [
            BatterySensor(coordinator, entry),
            ChargeTimeSensor(coordinator, entry),
            TyrePressureSensor(
                coordinator,
                entry,
                key="front_left_tyre",
                name="Front left tyre",
                unique_id_suffix="front_left_tyre",
            ),
            TyrePressureSensor(
                coordinator,
                entry,
                key="front_right_tyre",
                name="Front right tyre",
                unique_id_suffix="front_right_tyre",
            ),
            TyrePressureSensor(
                coordinator,
                entry,
                key="back_left_tyre",
                name="Back left tyre",
                unique_id_suffix="back_left_tyre",
            ),
            TyrePressureSensor(
                coordinator,
                entry,
                key="back_right_tyre",
                name="Back right tyre",
                unique_id_suffix="back_right_tyre",
            ),
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


class TyrePressureSensor(IraSensor):
    """One tyre pressure, in the same psi figure the iRA.ev app shows."""

    _attr_device_class = SensorDeviceClass.PRESSURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPressure.PSI
    _attr_suggested_unit_of_measurement = UnitOfPressure.PSI
    _attr_suggested_display_precision = 1
    _attr_icon = "mdi:tire"

    def __init__(
        self,
        coordinator: IraCoordinator,
        entry: ConfigEntry,
        *,
        key: str,
        name: str,
        unique_id_suffix: str,
    ) -> None:
        """Identify one tyre."""
        super().__init__(coordinator, entry)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{self._vehicle_id}_{unique_id_suffix}"

    @property
    def native_value(self) -> float | None:
        """Pressure in psi."""
        if self.coordinator.data is None:
            return None
        return getattr(self.coordinator.data, self._key)

    @property
    def available(self) -> bool:
        """Unavailable when the car has not reported this tyre."""
        return super().available and self.native_value is not None


def _keep_tyre_pressure_in_psi(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Show tyre pressure in psi even when Home Assistant uses metric units.

    A previous version let Home Assistant convert these readings to kPa.
    """
    vehicle_id = entry.data[CONF_VEHICLE_ID]
    registry = er.async_get(hass)
    for entity in registry.entities.values():
        if not entity.unique_id or not entity.unique_id.startswith(f"{vehicle_id}_"):
            continue
        if not entity.unique_id.endswith("_tyre"):
            continue
        sensor_options = dict(entity.options.get(SENSOR_DOMAIN, {}))
        if sensor_options.get("unit_of_measurement") in (None, UnitOfPressure.PSI):
            continue
        sensor_options["unit_of_measurement"] = UnitOfPressure.PSI
        registry.async_update_entity_options(
            entity.entity_id, SENSOR_DOMAIN, sensor_options
        )
