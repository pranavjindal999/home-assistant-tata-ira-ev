"""Turn iRA.ev payloads into sensor values and air-conditioning commands."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

AC_MINUTES_MIN = 0
AC_MINUTES_MAX = 30


def retry_wait_seconds(retry_after: str | None, attempt: int) -> float:
    """How long to wait before repeating a rate-limited or failed request.

    ``attempt`` starts at 1. A Retry-After header wins. Otherwise the wait
    doubles, and it never exceeds two minutes.
    """
    if retry_after:
        try:
            seconds = float(retry_after.strip())
        except ValueError:
            seconds = 0
        if seconds > 0:
            return min(seconds, 120)
    return float(min(2**attempt, 60))


@dataclass(frozen=True)
class VehicleStatus:
    """Battery, charging, air conditioning, and lock values for one car."""

    battery_percent: float | None
    charging: bool | None
    charge_minutes_remaining: int | None
    ac_on: bool | None = None
    locked: bool | None = None
    approach_lights: bool | None = None
    headlights: bool | None = None
    hazard_lights: bool | None = None
    engine_on: bool | None = None
    front_left_tyre: float | None = None
    front_right_tyre: float | None = None
    back_left_tyre: float | None = None
    back_right_tyre: float | None = None
    tyre_pressure_low: bool | None = None
    range_km: float | None = None
    aux_voltage: float | None = None
    service_days: float | None = None
    service_km: float | None = None
    charger_connected: bool | None = None
    aux_battery_low: bool | None = None
    car_warning: bool | None = None
    front_left_door: bool | None = None
    front_right_door: bool | None = None
    rear_left_door: bool | None = None
    rear_right_door: bool | None = None
    bonnet: bool | None = None
    tailgate: bool | None = None
    odometer_km: float | None = None
    speed_kmh: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    ignition_on: bool | None = None
    high_beam: bool | None = None
    low_beam: bool | None = None


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
        approach_lights=_optional_bool(results, "approchLampOnFlag"),
        headlights=_optional_bool(results, "positionLampOnFlag"),
        hazard_lights=_optional_bool(results, "hazardLampOnFlag"),
        engine_on=_optional_bool(results, "crankOn"),
        front_left_tyre=_optional_pressure(results, "frontLeftWheelTyrePressure"),
        front_right_tyre=_optional_pressure(results, "frontRightWheelTyrePressure"),
        back_left_tyre=_optional_pressure(results, "rearLeftWheelTyrePressure"),
        back_right_tyre=_optional_pressure(results, "rearRightWheelTyrePressure"),
        tyre_pressure_low=_tyre_pressure_low(results),
        range_km=_optional_number(results, "distanceToEmpty"),
        aux_voltage=_positive_number(results, "vehicleBatteryLevel"),
        service_days=_optional_number(results, "nextServiceDueDays"),
        service_km=_optional_number(results, "nextServiceDueKm"),
        charger_connected=_optional_bool(results, "hvChargerConnectFlag"),
        aux_battery_low=_optional_bool(results, "lowLvBattChargeFlag"),
        car_warning=_car_warning(results),
        front_left_door=_optional_bool(results, "leftFrontDoorOpenFlag"),
        front_right_door=_optional_bool(results, "rightFrontDoorOpenFlag"),
        rear_left_door=_optional_bool(results, "leftRearDoorOpenFlag"),
        rear_right_door=_optional_bool(results, "rightRearDoorOpenFlag"),
        bonnet=_optional_bool(results, "bonnetOpenFlag"),
        tailgate=_optional_bool(results, "tailGateOpenFlag"),
        high_beam=_optional_bool(results, "highBeamLampOnFlag"),
        low_beam=_optional_bool(results, "lowBeamLampOnFlag"),
    )


def _optional_pressure(results: dict[str, Any], key: str) -> float | None:
    """Read a tyre pressure in psi. Zero is the app's blank value."""
    if key not in results or results[key] is None or results[key] == "":
        return None
    try:
        value = float(results[key])
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return value


def _tyre_pressure_low(results: dict[str, Any]) -> bool | None:
    """True when the app would mark any tyre as low."""
    states = []
    for key in (
        "frontLeftWheelTyrePressureState",
        "frontRightWheelTyrePressureState",
        "rearLeftWheelTyrePressureState",
        "rearRightWheelTyrePressureState",
    ):
        if key not in results or results[key] is None:
            continue
        try:
            states.append(float(results[key]) == 1.0)
        except (TypeError, ValueError):
            continue
    if not states:
        return None
    return any(states)


def _optional_number(results: dict[str, Any], key: str) -> float | None:
    if key not in results or results[key] is None or results[key] == "":
        return None
    try:
        return float(results[key])
    except (TypeError, ValueError):
        return None


def _positive_number(results: dict[str, Any], key: str) -> float | None:
    value = _optional_number(results, key)
    if value is None or value <= 0:
        return None
    return value


def _car_warning(results: dict[str, Any]) -> bool | None:
    """True when the car reports a fault the app shows as a warning lamp."""
    seen = False
    warning = False
    for key in (
        "milLampOnFlag",
        "absStateFlag",
        "srsWarningLampFlag",
        "hvBatteryHighTempFlag",
        "transmissionMalfunctionFlag",
        "vCuMalfunctionFlag",
        "epasStateFlag",
        "driveMotorStatusFlag",
        "brakeVacuumPumpStatusFlag",
    ):
        if key not in results or results[key] is None:
            continue
        seen = True
        warning = warning or bool(results[key])
    for key in ("eVSystemWarning", "hVCriticalState"):
        value = _optional_number(results, key)
        if value is None:
            continue
        seen = True
        warning = warning or value != 0
    if not seen:
        return None
    return warning


def _optional_bool(results: dict[str, Any], key: str) -> bool | None:
    if key not in results or results[key] is None:
        return None
    return bool(results[key])


def parse_vehicle_details(payload: dict[str, Any]) -> dict[str, Any]:
    """Read odometer, speed, and location from vehicle state."""
    results = payload.get("results") or {}
    details: dict[str, Any] = {}
    ac_on = parse_air_conditioning(payload)
    if ac_on is not None:
        details["ac_on"] = ac_on
    odometer = _optional_number(results, "odometerInMeters")
    if odometer is not None and odometer > 0:
        details["odometer_km"] = round(odometer / 1000, 1)
    speed = _optional_number(results, "speed")
    if speed is not None:
        details["speed_kmh"] = speed
    ignition = _optional_bool(results, "ignitionOn")
    if ignition is not None:
        details["ignition_on"] = ignition
    latitude = _optional_number(results, "gpsLatitude")
    longitude = _optional_number(results, "gpsLongitude")
    if latitude not in (None, 0) and longitude not in (None, 0):
        details["latitude"] = latitude
        details["longitude"] = longitude
    return details


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
    Turning the air conditioner off sends an empty config object. A null config
    is rejected by the command service.
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
        {"config": {}, "commandTraceId": trace_id},
    )


def empty_command_body(trace_id: str) -> dict[str, Any]:
    """Body for a command that does not set a timer."""
    return {"config": {}, "commandTraceId": trace_id}


def timed_command_body(minutes: int, trace_id: str) -> dict[str, Any]:
    """Body for a command that runs for a number of minutes."""
    if minutes < AC_MINUTES_MIN or minutes > AC_MINUTES_MAX:
        raise ValueError(
            f"Duration must be {AC_MINUTES_MIN} to {AC_MINUTES_MAX} minutes"
        )
    return {
        "config": {"settimer": str(int(minutes) * 60)},
        "commandTraceId": trace_id,
    }


def lock_command_body(locked: bool, trace_id: str) -> tuple[str, dict[str, Any]]:
    """Build the lock or unlock command the iRA.ev app sends."""
    command = "LockVehicleCommand" if locked else "UnlockVehicleCommand"
    return command, {"config": {}, "commandTraceId": trace_id}


def command_log_body(vehicle_id: str, command: str, origin: str) -> dict[str, str]:
    """Ask iRA.ev for the command id the car command must use.

    The app sends this before lock, unlock, and air conditioning. The metadata
    value is the literal string the app builds, including the unquoted name.
    """
    return {
        "vehicleId": vehicle_id,
        "commandName": command,
        "originDateTime": origin,
        "metadata": "{" + command + ":true}",
    }


def parse_device_awake(payload: dict[str, Any]) -> bool | None:
    """Read whether the car's command unit is awake."""
    results = payload.get("results")
    if not isinstance(results, dict):
        return None
    awake = results.get("deviceState")
    if not isinstance(awake, bool):
        return None
    return awake


def parse_command_status(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    """Read a command's status and the id used to poll it."""
    results = payload.get("results")
    if isinstance(results, dict) and "status" not in results:
        nested = results.get("results")
        if isinstance(nested, dict):
            results = nested
    if not isinstance(results, dict):
        return None, None
    status = results.get("status")
    if not isinstance(status, str) or not status:
        status = None
    correlation = results.get("correlationId")
    if isinstance(correlation, int):
        correlation = str(correlation)
    elif not isinstance(correlation, str) or not correlation:
        correlation = None
    return status, correlation


def command_progress(status: str | None) -> str:
    """Classify a command status as done, wait, or failed.

    Only an explicit success is finished. Accepted, queued, and missing
    statuses are still running.
    """
    if not status:
        return "wait"
    normalized = status.strip().lower()
    if normalized in {"failure", "failed", "timed out", "timeout", "rejected"}:
        return "failed"
    if normalized in {
        "success",
        "successful",
        "completed",
        "complete",
        "executed",
        "done",
        "ok",
    }:
        return "done"
    return "wait"


def parse_command_log(payload: dict[str, Any]) -> tuple[str | None, bool | None]:
    """Read the command id and whether the car is connected."""
    results = payload.get("results")
    if not isinstance(results, dict):
        return None, None
    trace_id = results.get("commandTraceId")
    if not isinstance(trace_id, str) or not trace_id:
        trace_id = None
    connected = results.get("connectedStatus")
    if not isinstance(connected, bool):
        connected = None
    return trace_id, connected


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


def parse_auth_code(payload: dict[str, Any]) -> str | None:
    """Read the auth code returned with a verified sign-in code."""
    results = payload.get("results")
    if not isinstance(results, dict):
        return None
    auth_code = results.get("authCode")
    if not isinstance(auth_code, str) or not auth_code:
        return None
    return auth_code


def parse_user_type(payload: dict[str, Any]) -> str:
    """Read whether the phone belongs to an existing account."""
    results = payload.get("results")
    if isinstance(results, dict) and results.get("userType") in ("existing", "new"):
        return results["userType"]
    return "existing"


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


def merge_live_payload(previous: dict[str, Any] | None, payload: dict[str, Any]) -> dict[str, Any]:
    """Fold one live message into the signals already received."""
    merged = dict(previous or {})
    for key, value in payload.items():
        if key == "dynamicSignals" and isinstance(value, dict):
            current = merged.get("dynamicSignals")
            signals = dict(current) if isinstance(current, dict) else {}
            signals.update(value)
            merged["dynamicSignals"] = signals
        else:
            merged[key] = value
    return merged


def apply_lks_snapshot(
    current: VehicleStatus | None, payload: dict[str, Any]
) -> VehicleStatus:
    """Merge one last-known-state snapshot onto the latest car reading.

    Signals the snapshot leaves out stay as they were. Lock uses the same
    polarity as vehicle health: the signal is true when the car is unlocked.
    """
    base = current or VehicleStatus(None, None, None)
    updates: dict[str, Any] = {}
    battery = _live_number(payload, "V_Batt_HVBt_SoCPercn")
    if battery is not None:
        updates["battery_percent"] = battery
    charging = _live_flag(payload, "V_Batt_HVBt_ChargState")
    if charging is not None:
        updates["charging"] = charging
    remaining = _live_charge_minutes(base, payload, charging)
    if "charge_minutes_remaining" in remaining:
        updates["charge_minutes_remaining"] = remaining["charge_minutes_remaining"]
    locked = _live_flag(payload, "V_Secu_ACCS_VehLockSt")
    if locked is not None:
        updates["locked"] = not locked
    ac_on = _live_flag(payload, "V_Cabn_HVAC_ActivAc")
    if ac_on is not None:
        updates["ac_on"] = ac_on
    for signal, field in _LIVE_FLAGS.items():
        flag = _live_flag(payload, signal)
        if flag is not None:
            updates[field] = flag
    for signal, field in _LIVE_PRESSURES.items():
        pressure = _live_number(payload, signal)
        if pressure is not None and pressure > 0:
            updates[field] = pressure
    low = _live_tyre_low(payload)
    if low is not None:
        updates["tyre_pressure_low"] = low
    distance = _live_number(payload, "V_Pwtn_Emtr_DTeInfo")
    if distance is not None:
        updates["range_km"] = distance
    latitude = _live_number(payload, "V_Conn_Gloc_Latitude")
    longitude = _live_number(payload, "V_Conn_Gloc_Longitude")
    if latitude not in (None, 0) and longitude not in (None, 0):
        updates["latitude"] = latitude
        updates["longitude"] = longitude
    if not updates:
        return base
    return replace(base, **updates)


def note_live_command(
    payload: dict[str, Any] | None, field: str, expected: bool
) -> dict[str, Any] | None:
    """Keep a command in the live snapshot until the car reports it."""
    mapped = _LIVE_COMMANDS.get(field)
    if payload is None or mapped is None:
        return payload
    signal, invert = mapped
    updated = dict(payload)
    updated[signal] = {"value": (not expected) if invert else expected}
    return updated


_LIVE_FLAGS = {
    "V_Body_Lamp_ApproachOn": "approach_lights",
    "V_Body_Lamp_PosTTSign": "headlights",
    "V_Body_Lamp_HazSign": "hazard_lights",
    "V_Body_Lamp_LowBeamOn": "low_beam",
    "V_Cabn_Door_OpenR1LH": "front_left_door",
    "V_Cabn_Door_OpenR1RH": "front_right_door",
    "V_Cabn_Door_OpenR2LH": "rear_left_door",
    "V_Cabn_Door_OpenR2RH": "rear_right_door",
    "V_Body_Hood_FrunkOpen": "bonnet",
    "V_Body_Hood_TrunkOpen": "tailgate",
}

_LIVE_PRESSURES = {
    "V_Chas_Axle_TyrePressR1LH": "front_left_tyre",
    "V_Chas_Axle_TyrePressR1RH": "front_right_tyre",
    "V_Chas_Axle_TyrePressR2LH": "back_left_tyre",
    "V_Chas_Axle_TyrePressR2RH": "back_right_tyre",
}

_LIVE_COMMANDS = {
    "ac_on": ("V_Cabn_HVAC_ActivAc", False),
    "approach_lights": ("V_Body_Lamp_ApproachOn", False),
    "headlights": ("V_Body_Lamp_PosTTSign", False),
    "hazard_lights": ("V_Body_Lamp_HazSign", False),
    "locked": ("V_Secu_ACCS_VehLockSt", True),
}

_LIVE_TYRE_LOW = (
    "V_Chas_Axle_TyrePressLowR1LH",
    "V_Chas_Axle_TyrePressLowR1RH",
    "V_Chas_Axle_TyrePressLowR2LH",
    "V_Chas_Axle_TyrePressLowR2RH",
)


def _live_signal(payload: dict[str, Any], name: str) -> Any:
    if name in payload:
        raw = payload.get(name)
    else:
        dynamic = payload.get("dynamicSignals")
        raw = dynamic.get(name) if isinstance(dynamic, dict) else None
    if isinstance(raw, dict):
        return raw.get("value")
    return raw


def _live_flag(payload: dict[str, Any], name: str) -> bool | None:
    value = _live_signal(payload, name)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value in (0, 1):
        return bool(value)
    if isinstance(value, str) and value.lower() in ("true", "false"):
        return value.lower() == "true"
    return None


def _live_number(payload: dict[str, Any], name: str) -> float | None:
    value = _live_signal(payload, name)
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _live_charge_minutes(
    current: VehicleStatus, payload: dict[str, Any], charging: bool | None
) -> dict[str, Any]:
    if charging is False:
        return {"charge_minutes_remaining": None}
    hours = _live_number(payload, "V_Batt_HVBt_TtoChngHVHr")
    minutes = _live_number(payload, "V_Batt_HVBt_TtoChngHVMin")
    if hours is None and minutes is None:
        return {}
    carried = current.charge_minutes_remaining or 0
    carried_hours, carried_minutes = divmod(int(carried), 60)
    hour_value = carried_hours if hours is None else int(hours)
    minute_value = carried_minutes if minutes is None else int(minutes)
    return {"charge_minutes_remaining": hour_value * 60 + minute_value}


def _live_tyre_low(payload: dict[str, Any]) -> bool | None:
    flags = [_live_flag(payload, name) for name in _LIVE_TYRE_LOW]
    known = [flag for flag in flags if flag is not None]
    if not known:
        return None
    if any(known):
        return True
    if len(known) == len(_LIVE_TYRE_LOW):
        return False
    return None


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
