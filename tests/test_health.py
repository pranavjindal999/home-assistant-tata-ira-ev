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
command_log_body = _MODULE.command_log_body
parse_command_log = _MODULE.parse_command_log
service_error = _MODULE.service_error


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
        self.assertIsNone(body["config"])
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
        self.assertIsNone(body["config"])
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


if __name__ == "__main__":
    unittest.main()
