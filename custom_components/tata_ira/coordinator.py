"""Poll battery and charging status for one Tata EV."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import IraAuthError, IraClient, IraConnectionError, IraError
from .parser import VehicleStatus
from .const import CONF_REFRESH_TOKEN, DOMAIN, POLL_INTERVAL

_LOGGER = logging.getLogger(__name__)


class IraCoordinator(DataUpdateCoordinator[VehicleStatus]):
    """Battery percentage, charging state, and time remaining."""

    def __init__(
        self, hass: HomeAssistant, client: IraClient, entry: ConfigEntry
    ) -> None:
        """Poll the car every few minutes."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=POLL_INTERVAL,
        )
        self.client = client
        self.entry = entry

    async def _async_update_data(self) -> VehicleStatus:
        try:
            status, rotated = await self.client.async_vehicle_status()
        except (IraAuthError, IraConnectionError, IraError) as err:
            raise UpdateFailed(str(err) or err.__class__.__name__) from err
        if rotated and self.entry.data.get(CONF_REFRESH_TOKEN) != rotated:
            self.hass.config_entries.async_update_entry(
                self.entry,
                data={**self.entry.data, CONF_REFRESH_TOKEN: rotated},
            )
        return status
