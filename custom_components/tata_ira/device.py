"""Shared device identity for the car."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo

from .const import CONF_VEHICLE_ID, DOMAIN


def vehicle_device_info(entry: ConfigEntry) -> DeviceInfo:
    """The Tata EV these sensors belong to."""
    vehicle_id = entry.data[CONF_VEHICLE_ID]
    return DeviceInfo(
        identifiers={(DOMAIN, vehicle_id)},
        manufacturer="Tata Motors",
        model="iRA.ev",
        name="Tata iRA.ev",
    )
