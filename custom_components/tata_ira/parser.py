"""Turn iRA.ev payloads into sensor values and air-conditioning commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

AC_MINUTES_MIN = 0
AC_MINUTES_MAX = 30


@dataclass(frozen=True)
class VehicleStatus:
    """Battery, charging, air conditioning, and lock values for one car."""

    battery_percent: float | None
    charging: bool | None
    charge_minutes_remaining: int | None
    ac_on: bool | None = None
    locked: bool | None = None


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
    # The app shows "locked" when vehicleLockState is false.
    lock_state = results.get("vehicleLockState")
    return VehicleStatus(
        battery_percent=None if battery is None else float(battery),
        charging=None if charging is None else bool(charging),
        charge_minutes_remaining=remaining,
        locked=None if lock_state is None else not bool(lock_state),
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


def lock_command_body(locked: bool, trace_id: str) -> tuple[str, dict[str, Any]]:
    """Build the lock or unlock command the iRA.ev app sends."""
    command = "LockVehicleCommand" if locked else "UnlockVehicleCommand"
    return command, {"config": None, "commandTraceId": trace_id}


def service_error(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return the service error message and code, when the body contains one."""
    error = payload.get("errorData")
    if not isinstance(error, dict):
        return None, None
    items = error.get("errorList")
    if not isinstance(items, list) or not items or not isinstance(items[0], dict):
        return "iRA.ev rejected the request", None
    message = items[0].get("errorMsg")
    code = items[0].get("errorCode")
    if not isinstance(message, str) or not message:
        message = "iRA.ev rejected the request"
    if not isinstance(code, str) or not code:
        code = None
    return message, code


def parse_ref_id(payload: dict[str, Any]) -> str | None:
    """Read the reference id returned when a sign-in code is sent."""
    results = payload.get("results")
    if not isinstance(results, dict):
        return None
    ref_id = results.get("refId")
    if not isinstance(ref_id, str) or not ref_id:
        return None
    return ref_id


def parse_code_verifier(payload: dict[str, Any]) -> str | None:
    """Read the verifier returned after the sign-in code is accepted."""
    results = payload.get("results")
    if not isinstance(results, dict):
        return None
    verifier = results.get("codeVerifier")
    if not isinstance(verifier, str) or not verifier:
        return None
    return verifier


def parse_login_tokens(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return the access token and refresh token from a sign-in response."""
    results = payload.get("results")
    if not isinstance(results, dict):
        results = {}
    details = results.get("accessTokenDetails")
    if not isinstance(details, dict):
        details = results
    access_token = details.get("accessToken") or payload.get("accessToken")
    refresh_token = details.get("refreshToken") or payload.get("refreshToken")
    if not isinstance(access_token, str) or not access_token:
        return None, None
    if not isinstance(refresh_token, str) or not refresh_token:
        return access_token, None
    return access_token, refresh_token


def parse_vehicle_ids(payload: dict[str, Any]) -> list[str]:
    """Return the chassis ids of cars on the signed-in account."""
    results = payload.get("results")
    if not isinstance(results, dict):
        return []
    vehicles = results.get("vehicles")
    if not isinstance(vehicles, list):
        return []
    ids: list[str] = []
    for vehicle in vehicles:
        if not isinstance(vehicle, dict):
            continue
        chassis = vehicle.get("chassisNumber")
        if isinstance(chassis, str) and chassis and chassis not in ids:
            ids.append(chassis)
    return ids


def otp_verify_body(
    country_code: str, phone: str, otp: str, ref_id: str
) -> dict[str, Any]:
    """Build the sign-in code request the iRA.ev app sends."""
    return {
        "countryCode": country_code,
        "phone": phone,
        "otp": otp,
        "refId": ref_id,
        "redirectUrl": "https://prod-ev.tatamotors.com/",
        "consentType": "Explicit",
        "programTnC": True,
        "privacyPolicyAccepted": True,
        "marketingCommunication": False,
        "loyalCustomer": "Y",
        "storeId": "store_id",
    }
