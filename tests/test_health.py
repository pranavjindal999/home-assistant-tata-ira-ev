"""Parser tests for iRA.ev vehicle health."""

from __future__ import annotations

import unittest

import importlib.util
import sys
from pathlib import Path

_PARSER = Path(__file__).parents[1] / "custom_components" / "tata_ira" / "parser.py"
_SPEC = importlib.util.spec_from_file_location("tata_ira_parser", _PARSER)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules["tata_ira_parser"] = _MODULE
_SPEC.loader.exec_module(_MODULE)
parse_vehicle_health = _MODULE.parse_vehicle_health
parse_air_conditioning = _MODULE.parse_air_conditioning
parse_vehicle_details = _MODULE.parse_vehicle_details
parse_refresh_tokens = _MODULE.parse_refresh_tokens
parse_ref_id = _MODULE.parse_ref_id
parse_code_verifier = _MODULE.parse_code_verifier
parse_auth_code = _MODULE.parse_auth_code
parse_user_type = _MODULE.parse_user_type
parse_login_tokens = _MODULE.parse_login_tokens
parse_vehicle_ids = _MODULE.parse_vehicle_ids
otp_verify_body = _MODULE.otp_verify_body
ac_command_body = _MODULE.ac_command_body
lock_command_body = _MODULE.lock_command_body
empty_command_body = _MODULE.empty_command_body
timed_command_body = _MODULE.timed_command_body
command_log_body = _MODULE.command_log_body
parse_command_log = _MODULE.parse_command_log
parse_command_status = _MODULE.parse_command_status
parse_device_awake = _MODULE.parse_device_awake
command_progress = _MODULE.command_progress
service_error = _MODULE.service_error
retry_wait_seconds = _MODULE.retry_wait_seconds


class ParseVehicleHealthTests(unittest.TestCase):
    def test_charging_session_includes_remaining_minutes(self) -> None:
        status = parse_vehicle_health(
            {
                "results": {
                    "hvBatterySocPercentage": 64.5,
                    "hvChargingState": True,
                    "timeToChargeHour": 1,
                    "timeToChargeMinute": 20,
                }
            }
        )
        self.assertEqual(status.battery_percent, 64.5)
        self.assertTrue(status.charging)
        self.assertEqual(status.charge_minutes_remaining, 80)

    def test_idle_car_has_no_charge_timer(self) -> None:
        status = parse_vehicle_health(
            {
                "results": {
                    "hvBatterySocPercentage": 80,
                    "hvChargingState": False,
                    "timeToChargeHour": 0,
                    "timeToChargeMinute": 0,
                }
            }
        )
        self.assertEqual(status.battery_percent, 80)
        self.assertFalse(status.charging)
        self.assertIsNone(status.charge_minutes_remaining)

    def test_missing_results_are_empty(self) -> None:
        status = parse_vehicle_health({})
        self.assertIsNone(status.battery_percent)
        self.assertIsNone(status.charging)
        self.assertIsNone(status.charge_minutes_remaining)
        self.assertIsNone(status.ac_on)
        self.assertIsNone(status.locked)

    def test_lock_state_false_means_locked(self) -> None:
        locked = parse_vehicle_health({"results": {"vehicleLockState": False}})
        unlocked = parse_vehicle_health({"results": {"vehicleLockState": True}})
        self.assertTrue(locked.locked)
        self.assertFalse(unlocked.locked)

    def test_light_and_engine_flags(self) -> None:
        status = parse_vehicle_health(
            {
                "results": {
                    "approchLampOnFlag": True,
                    "positionLampOnFlag": False,
                    "hazardLampOnFlag": True,
                    "crankOn": False,
                }
            }
        )
        self.assertTrue(status.approach_lights)
        self.assertFalse(status.headlights)
        self.assertTrue(status.hazard_lights)
        self.assertFalse(status.engine_on)
        self.assertIsNone(status.front_left_tyre)
        self.assertEqual(empty_command_body("trace")["config"], {})
        self.assertEqual(timed_command_body(10, "trace")["config"]["settimer"], "600")

    def test_tyre_pressures_are_psi_and_zero_is_blank(self) -> None:
        status = parse_vehicle_health(
            {
                "results": {
                    "frontLeftWheelTyrePressure": 36.8,
                    "frontRightWheelTyrePressure": "39.2",
                    "rearLeftWheelTyrePressure": 38.4,
                    "rearRightWheelTyrePressure": 0,
                    "frontLeftWheelTyrePressureState": 0,
                    "frontRightWheelTyrePressureState": 1,
                    "rearLeftWheelTyrePressureState": 0,
                    "rearRightWheelTyrePressureState": 0,
                    "spareTyrePressure": 0,
                }
            }
        )
        self.assertEqual(status.front_left_tyre, 36.8)
        self.assertEqual(status.front_right_tyre, 39.2)
        self.assertEqual(status.back_left_tyre, 38.4)
        self.assertIsNone(status.back_right_tyre)
        self.assertTrue(status.tyre_pressure_low)

    def test_extra_health_details(self) -> None:
        status = parse_vehicle_health(
            {
                "results": {
                    "distanceToEmpty": 59,
                    "hvBatterySohPercentage": 0,
                    "vehicleBatteryLevel": 13.7,
                    "nextServiceDueDays": 73,
                    "nextServiceDueKm": 3199,
                    "hvChargerConnectFlag": False,
                    "lowLvBattChargeFlag": False,
                    "milLampOnFlag": False,
                    "leftFrontDoorOpenFlag": True,
                    "rightFrontDoorOpenFlag": False,
                    "bonnetOpenFlag": False,
                    "tailGateOpenFlag": False,
                }
            }
        )
        self.assertEqual(status.range_km, 59)
        self.assertEqual(status.aux_voltage, 13.7)
        self.assertEqual(status.service_days, 73)
        self.assertEqual(status.service_km, 3199)
        self.assertFalse(status.charger_connected)
        self.assertFalse(status.aux_battery_low)
        self.assertFalse(status.car_warning)
        self.assertTrue(status.front_left_door)
        self.assertFalse(status.bonnet)
        self.assertIsNone(status.rear_left_door)

    def test_warning_lamp(self) -> None:
        status = parse_vehicle_health(
            {"results": {"milLampOnFlag": True, "eVSystemWarning": 0}}
        )
        self.assertTrue(status.car_warning)

    def test_vehicle_state_details(self) -> None:
        details = parse_vehicle_details(
            {
                "results": {
                    "airConditionOn": True,
                    "odometerInMeters": "23144317",
                    "speed": 0,
                    "ignitionOn": False,
                    "gpsLatitude": 0,
                    "gpsLongitude": 0,
                }
            }
        )
        self.assertTrue(details["ac_on"])
        self.assertEqual(details["odometer_km"], 23144.3)
        self.assertEqual(details["speed_kmh"], 0)
        self.assertFalse(details["ignition_on"])
        self.assertNotIn("latitude", details)

    def test_beams(self) -> None:
        status = parse_vehicle_health(
            {
                "results": {
                    "highBeamLampOnFlag": False,
                    "lowBeamLampOnFlag": True,
                }
            }
        )
        self.assertFalse(status.high_beam)
        self.assertTrue(status.low_beam)


class AirConditioningTests(unittest.TestCase):
    def test_vehicle_state_reports_air_conditioning(self) -> None:
        self.assertFalse(parse_air_conditioning({"results": {"airConditionOn": False}}))
        self.assertTrue(parse_air_conditioning({"results": {"acState": True}}))
        self.assertIsNone(parse_air_conditioning({"results": {}}))

    def test_start_sends_duration_in_seconds(self) -> None:
        command, body = ac_command_body(True, 10, "trace-1")
        self.assertEqual(command, "StartAcCommand")
        self.assertEqual(body["config"]["settimer"], "600")
        self.assertEqual(body["commandTraceId"], "trace-1")

    def test_zero_minutes_is_allowed(self) -> None:
        command, body = ac_command_body(True, 0, "trace-0")
        self.assertEqual(command, "StartAcCommand")
        self.assertEqual(body["config"]["settimer"], "0")

    def test_duration_above_thirty_minutes_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ac_command_body(True, 31, "trace-2")

    def test_stop_clears_the_timer(self) -> None:
        command, body = ac_command_body(False, 10, "trace-3")
        self.assertEqual(command, "StopAcCommand")
        self.assertEqual(body["config"], {})
        self.assertEqual(body["commandTraceId"], "trace-3")

    def test_refresh_accepts_top_level_and_nested_tokens(self) -> None:
        self.assertEqual(
            parse_refresh_tokens({"accessToken": "access", "expires_in": 3600}),
            ("access", None),
        )
        self.assertEqual(
            parse_refresh_tokens(
                {"results": {"accessToken": "access", "refreshToken": "next"}}
            ),
            ("access", "next"),
        )

    def test_sign_in_reads_the_code_verifier_and_session(self) -> None:
        self.assertEqual(parse_ref_id({"results": {"refId": "ref-1"}}), "ref-1")
        self.assertIsNone(parse_ref_id({"results": {}}))
        self.assertEqual(
            parse_code_verifier({"results": {"codeVerifier": "verifier"}}),
            "verifier",
        )
        self.assertEqual(
            parse_auth_code({"results": {"authCode": "auth"}}),
            "auth",
        )
        self.assertEqual(
            parse_user_type({"results": {"userType": "new"}}),
            "new",
        )
        self.assertEqual(parse_user_type({"results": {}}), "existing")
        self.assertEqual(
            parse_login_tokens(
                {
                    "results": {
                        "accessTokenDetails": {
                            "accessToken": "access",
                            "refreshToken": "refresh",
                        }
                    }
                }
            ),
            ("access", "refresh"),
        )
        self.assertEqual(
            parse_vehicle_ids(
                {
                    "results": {
                        "vehicles": [
                            {"chassisNumber": "CAR1"},
                            {"chassisNumber": ""},
                            {"chassisNumber": "CAR1"},
                            {"vehicleName": "ignored"},
                        ]
                    }
                }
            ),
            ["CAR1"],
        )
        body = otp_verify_body("91", "9000000000", "123456", "ref-1")
        self.assertEqual(body["otp"], "123456")
        self.assertEqual(body["refId"], "ref-1")
        self.assertEqual(body["consentType"], "Explicit")

    def test_lock_and_unlock_commands(self) -> None:
        command, body = lock_command_body(True, "trace-lock")
        self.assertEqual(command, "LockVehicleCommand")
        self.assertEqual(body["config"], {})
        command, body = lock_command_body(False, "trace-unlock")
        self.assertEqual(command, "UnlockVehicleCommand")
        self.assertEqual(body["commandTraceId"], "trace-unlock")

    def test_command_log_uses_the_server_id(self) -> None:
        body = command_log_body("CAR1", "LockVehicleCommand", "2026-10-24T18:00:00")
        self.assertEqual(body["commandName"], "LockVehicleCommand")
        self.assertEqual(body["metadata"], "{LockVehicleCommand:true}")
        trace_id, connected = parse_command_log(
            {
                "results": {
                    "commandTraceId": "trace-from-server",
                    "connectedStatus": True,
                }
            }
        )
        self.assertEqual(trace_id, "trace-from-server")
        self.assertTrue(connected)
        message, code = service_error(
            {
                "results": None,
                "errorData": {
                    "errorList": [{"errorCode": "503", "errorMsg": "unavailable"}]
                },
            }
        )
        self.assertEqual(message, "unavailable")
        self.assertEqual(code, "503")
        self.assertTrue(parse_device_awake({"results": {"deviceState": True}}))
        status, correlation = parse_command_status(
            {"results": {"status": "In Progress", "correlationId": 42}}
        )
        self.assertEqual(status, "In Progress")
        self.assertEqual(correlation, "42")
        self.assertEqual(command_progress("accepted"), "wait")
        self.assertEqual(command_progress("in progress"), "wait")
        self.assertEqual(command_progress(""), "wait")
        self.assertEqual(command_progress(None), "wait")
        self.assertEqual(command_progress("success"), "done")
        self.assertEqual(command_progress("Success"), "done")
        self.assertEqual(command_progress("failure"), "failed")

    def test_retry_wait_honors_retry_after_and_backs_off(self) -> None:
        self.assertEqual(retry_wait_seconds("15", 1), 15)
        self.assertEqual(retry_wait_seconds(" 2 ", 4), 2)
        self.assertEqual(retry_wait_seconds("not-a-number", 1), 2)
        self.assertEqual(retry_wait_seconds(None, 1), 2)
        self.assertEqual(retry_wait_seconds(None, 3), 8)
        self.assertEqual(retry_wait_seconds("500", 1), 120)


if __name__ == "__main__":
    unittest.main()
