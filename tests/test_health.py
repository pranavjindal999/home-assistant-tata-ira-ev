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


if __name__ == "__main__":
    unittest.main()
