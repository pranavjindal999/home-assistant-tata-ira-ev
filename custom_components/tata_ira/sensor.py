"""Battery percentage and remaining charge time."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTime,
)
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
            *(
                ReadingSensor(coordinator, entry, **spec)
                for spec in _READINGS
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


_READINGS = (
    {
        "key": "range_km",
        "name": "Range",
        "unique_id_suffix": "range",
        "device_class": SensorDeviceClass.DISTANCE,
        "unit": UnitOfLength.KILOMETERS,
        "precision": 0,
        "icon": "mdi:map-marker-distance",
    },
    {
        "key": "odometer_km",
        "name": "Odometer",
        "unique_id_suffix": "odometer",
        "device_class": SensorDeviceClass.DISTANCE,
        "unit": UnitOfLength.KILOMETERS,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "precision": 1,
        "icon": "mdi:counter",
    },
    {
        "key": "aux_voltage",
        "name": "12V battery",
        "unique_id_suffix": "aux_battery",
        "device_class": SensorDeviceClass.VOLTAGE,
        "unit": UnitOfElectricPotential.VOLT,
        "precision": 1,
        "icon": "mdi:car-battery",
    },
    {
        "key": "service_days",
        "name": "Service due",
        "unique_id_suffix": "service_due",
        "device_class": SensorDeviceClass.DURATION,
        "unit": UnitOfTime.DAYS,
        "precision": 0,
        "icon": "mdi:calendar-clock",
    },
    {
        "key": "service_km",
        "name": "Service distance",
        "unique_id_suffix": "service_distance",
        "device_class": SensorDeviceClass.DISTANCE,
        "unit": UnitOfLength.KILOMETERS,
        "precision": 0,
        "icon": "mdi:wrench-clock",
    },
    {
        "key": "speed_kmh",
        "name": "Speed",
        "unique_id_suffix": "speed",
        "device_class": SensorDeviceClass.SPEED,
        "unit": UnitOfSpeed.KILOMETERS_PER_HOUR,
        "precision": 0,
    },
)


class ReadingSensor(IraSensor):
    """One numeric detail from the car."""

    def __init__(
        self,
        coordinator: IraCoordinator,
        entry: ConfigEntry,
        *,
        key: str,
        name: str,
        unique_id_suffix: str,
        device_class: SensorDeviceClass | None = None,
        unit: str | None = None,
        state_class: SensorStateClass = SensorStateClass.MEASUREMENT,
        precision: int | None = None,
        icon: str | None = None,
    ) -> None:
        """Identify one reading."""
        super().__init__(coordinator, entry)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{self._vehicle_id}_{unique_id_suffix}"
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = state_class
        self._attr_suggested_display_precision = precision
        self._attr_icon = icon

    @property
    def native_value(self) -> float | None:
        """The latest reading, or none when the car did not report it."""
        if self.coordinator.data is None:
            return None
        return getattr(self.coordinator.data, self._key)

    @property
    def available(self) -> bool:
        """Unavailable until this value has been reported."""
        return super().available and self.native_value is not None


class TyrePressureSensor(IraSensor):
    """One tyre pressure, in the same psi figure the iRA.ev app shows."""

    _attr_device_class = SensorDeviceClass.PRESSURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPressure.PSI
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
