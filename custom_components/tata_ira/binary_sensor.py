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
    async_add_entities(
        [
            ChargingSensor(coordinator, entry),
            ConnectedSensor(coordinator, entry),
            TyrePressureSensor(coordinator, entry),
            *(FlagSensor(coordinator, entry, *spec) for spec in _FLAGS),
        ]
    )


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


class ConnectedSensor(CoordinatorEntity[IraCoordinator], BinarySensorEntity):
    """On while the car's command link is awake."""

    _attr_has_entity_name = True
    _attr_name = "Connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: IraCoordinator, entry: ConfigEntry) -> None:
        """Identify the connection sensor."""
        super().__init__(coordinator)
        vehicle_id = entry.data[CONF_VEHICLE_ID]
        self._attr_unique_id = f"{vehicle_id}_connected"
        self._attr_device_info = vehicle_device_info(entry)

    @property
    def available(self) -> bool:
        """Available once a connection check has finished."""
        return self.coordinator.connected is not None

    @property
    def is_on(self) -> bool | None:
        """True while commands can reach the car without waiting for it to wake."""
        return self.coordinator.connected


class TyrePressureSensor(CoordinatorEntity[IraCoordinator], BinarySensorEntity):
    """On when the app would mark a tyre pressure as low."""

    _attr_has_entity_name = True
    _attr_name = "Tyre pressure"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:tire"

    def __init__(self, coordinator: IraCoordinator, entry: ConfigEntry) -> None:
        """Identify the tyre-pressure warning."""
        super().__init__(coordinator)
        vehicle_id = entry.data[CONF_VEHICLE_ID]
        self._attr_unique_id = f"{vehicle_id}_tyre_pressure"
        self._attr_device_info = vehicle_device_info(entry)

    @property
    def available(self) -> bool:
        """Available once the car has reported tyre status."""
        return (
            super().available
            and self.coordinator.data is not None
            and self.coordinator.data.tyre_pressure_low is not None
        )

    @property
    def is_on(self) -> bool | None:
        """True when any tyre is low."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.tyre_pressure_low


_FLAGS = (
    ("charger_connected", "Charger connected", BinarySensorDeviceClass.PLUG, "charger"),
    ("aux_battery_low", "12V battery low", BinarySensorDeviceClass.PROBLEM, "aux_battery_low"),
    ("car_warning", "Warning", BinarySensorDeviceClass.PROBLEM, "warning"),
    ("front_left_door", "Front left door", BinarySensorDeviceClass.DOOR, "front_left_door"),
    ("front_right_door", "Front right door", BinarySensorDeviceClass.DOOR, "front_right_door"),
    ("rear_left_door", "Rear left door", BinarySensorDeviceClass.DOOR, "rear_left_door"),
    ("rear_right_door", "Rear right door", BinarySensorDeviceClass.DOOR, "rear_right_door"),
    ("bonnet", "Bonnet", BinarySensorDeviceClass.DOOR, "bonnet"),
    ("tailgate", "Tailgate", BinarySensorDeviceClass.DOOR, "tailgate"),
)


class FlagSensor(CoordinatorEntity[IraCoordinator], BinarySensorEntity):
    """A yes-or-no detail from the car."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IraCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
        device_class: BinarySensorDeviceClass,
        unique_id_suffix: str,
    ) -> None:
        """Identify one flag."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_device_class = device_class
        vehicle_id = entry.data[CONF_VEHICLE_ID]
        self._attr_unique_id = f"{vehicle_id}_{unique_id_suffix}"
        self._attr_device_info = vehicle_device_info(entry)

    @property
    def available(self) -> bool:
        """Available once the car has reported this flag."""
        return super().available and self.is_on is not None

    @property
    def is_on(self) -> bool | None:
        """True when the car reports this condition."""
        if self.coordinator.data is None:
            return None
        return getattr(self.coordinator.data, self._key)
