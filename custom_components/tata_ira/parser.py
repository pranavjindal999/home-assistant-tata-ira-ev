"""Turn an iRA.ev vehicle-health payload into sensor values."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class VehicleStatus:
    """Battery and charging values for one car."""

    battery_percent: float | None
    charging: bool | None
    charge_minutes_remaining: int | None


def parse_vehicle_health(payload: dict[str, Any]) -> VehicleStatus:
    """Turn a vehicle-health response into battery and charging values."""
    results = payload.get("results") or {}
    battery = results.get("hvBatterySocPercentage")
    charging = results.get("hvChargingState")
    hours = results.get("timeToChargeHour")
    minutes = results.get("timeToChargeMinute")
    remaining = None
    if charging and hours is not None and minutes is not None:
        remaining = int(hours) * 60 + int(minutes)
    return VehicleStatus(
        battery_percent=None if battery is None else float(battery),
        charging=None if charging is None else bool(charging),
        charge_minutes_remaining=remaining,
    )
