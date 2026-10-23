"""Tata iRA.ev battery and charging status for Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IraClient
from .const import CONF_API_KEY, CONF_REFRESH_TOKEN, CONF_VEHICLE_ID, DOMAIN
from .coordinator import IraCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Connect to the car and expose battery and charging sensors."""
    client = IraClient(
        async_get_clientsession(hass),
        entry.data[CONF_REFRESH_TOKEN],
        entry.data[CONF_VEHICLE_ID],
        entry.data[CONF_API_KEY],
    )
    coordinator = IraCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Remove the car sensors."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
