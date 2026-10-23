"""Lock and unlock the car, and show whether it is locked."""

from __future__ import annotations

from homeassistant.components.lock import LockEntity
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
    """Add the car lock."""
    coordinator: IraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CarLock(coordinator, entry)])


class CarLock(CoordinatorEntity[IraCoordinator], LockEntity):
    """Shows locked or unlocked, and sends the matching command."""

    _attr_has_entity_name = True
    _attr_name = "Lock"

    def __init__(self, coordinator: IraCoordinator, entry: ConfigEntry) -> None:
        """Identify the lock."""
        super().__init__(coordinator)
        vehicle_id = entry.data[CONF_VEHICLE_ID]
        self._attr_unique_id = f"{vehicle_id}_lock"
        self._attr_device_info = vehicle_device_info(entry)

    @property
    def is_locked(self) -> bool | None:
        """True while the car reports that it is locked."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.locked

    async def async_lock(self, **kwargs: object) -> None:
        """Lock the car."""
        await self._async_set(True)

    async def async_unlock(self, **kwargs: object) -> None:
        """Unlock the car."""
        await self._async_set(False)

    async def _async_set(self, locked: bool) -> None:
        try:
            await self.coordinator.async_set_locked(locked)
        except UpdateFailed as err:
            raise HomeAssistantError(str(err)) from err
