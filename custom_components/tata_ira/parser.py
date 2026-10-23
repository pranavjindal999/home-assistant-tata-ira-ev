"""Turn iRA.ev payloads into sensor values and air-conditioning commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

AC_MINUTES_MIN = 0
AC_MINUTES_MAX = 30


@dataclass(frozen=True)
class VehicleStatus:
    """Battery, charging, and air-conditioning values for one car."""

    battery_percent: float | None
    charging: bool | None
    charge_minutes_remaining: int | None
    ac_on: bool | None = None


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


def parse_air_conditioning(payload: dict[str, Any]) -> bool | None:
    """Read whether the cabin air conditioner is on."""
    results = payload.get("results") or {}
    value = results.get("airConditionOn")
    if value is None:
        value = results.get("acState")
    if value is None:
        return None
    return bool(value)


def parse_refresh_tokens(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return the access token and a rotated refresh token, if present."""
    results = payload.get("results")
    if not isinstance(results, dict):
        results = {}
    access_token = results.get("accessToken") or payload.get("accessToken")
    if not isinstance(access_token, str) or not access_token:
        return None, None
    rotated = results.get("refreshToken") or payload.get("refreshToken")
    if not isinstance(rotated, str) or not rotated:
        rotated = None
    return access_token, rotated


def ac_command_body(on: bool, minutes: int, trace_id: str) -> tuple[str, dict[str, Any]]:
    """Build the vehicle-command name and body the iRA.ev app sends.

    The app stores the chosen minutes as seconds and sends that number in settimer.
    Turning the air conditioner off sends an empty config.
    """
    if on:
        if minutes < AC_MINUTES_MIN or minutes > AC_MINUTES_MAX:
            raise ValueError(
                f"Air conditioning duration must be {AC_MINUTES_MIN} to {AC_MINUTES_MAX} minutes"
            )
        return (
            "StartAcCommand",
            {
                "config": {"settimer": str(int(minutes) * 60)},
                "commandTraceId": trace_id,
            },
        )
    return (
        "StopAcCommand",
        {"config": None, "commandTraceId": trace_id},
    )
