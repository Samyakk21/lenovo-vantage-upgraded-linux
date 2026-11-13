#!/usr/bin/env python3
"""Unit tests for the battery charge-mode backend.

These tests never touch real sysfs: the charge_types path is replaced with an
in-memory fake that mimics the kernel's bracketed output.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daemon"))

from features import battery  # noqa: E402


class FakeChargeTypes:
    """Minimal stand-in for the kernel's bracketed charge_types file."""

    def __init__(self, active="Standard", available=("Standard", "Fast", "Long_Life")):
        self.active = active
        self.available = list(available)

    def exists(self):
        return True

    def read_text(self):
        rendered = []
        for mode in self.available:
            rendered.append(f"[{mode}]" if mode == self.active else mode)
        return " ".join(rendered) + "\n"

    def write_text(self, data):
        value = data.strip()
        if value not in self.available:
            raise ValueError(f"invalid charge type: {value}")
        self.active = value
        return len(data)


class ChargeTypesParserTests(unittest.TestCase):
    def test_active_mode_is_bracketed(self):
        available, active = battery.parse_charge_types("[Fast] Standard Long_Life")
        self.assertEqual(available, ["standard", "long_life", "fast"])
        self.assertEqual(active, "fast")

    def test_standard_active(self):
        available, active = battery.parse_charge_types("[Standard] Fast Long_Life")
        self.assertEqual(available, ["standard", "long_life", "fast"])
        self.assertEqual(active, "standard")

    def test_rapid_not_supported(self):
        available, active = battery.parse_charge_types("[Long_Life] Standard")
        self.assertEqual(available, ["standard", "long_life"])
        self.assertEqual(active, "long_life")

    def test_unknown_values_are_ignored(self):
        available, active = battery.parse_charge_types("N/A")
        self.assertEqual(available, [])
        self.assertIsNone(active)

    def test_aliases(self):
        self.assertEqual(battery.normalize_charge_mode("normal"), "standard")
        self.assertEqual(battery.normalize_charge_mode("conservation"), "long_life")
        self.assertEqual(battery.normalize_charge_mode("rapid"), "fast")
        self.assertEqual(battery.normalize_charge_mode("Rapid Charge"), "fast")
        with self.assertRaises(ValueError):
            battery.normalize_charge_mode("turbo")


class SetChargeModeTests(unittest.TestCase):
    def setUp(self):
        self.charge_types = FakeChargeTypes()
        self.patcher = patch.object(battery, "get_charge_types_path", return_value=self.charge_types)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_set_rapid_charge_writes_fast(self):
        battery.set_rapid_charge(True)
        self.assertEqual(self.charge_types.active, "Fast")
        self.assertTrue(battery.get_rapid_charge())

    def test_set_conservation_writes_long_life(self):
        battery.set_conservation(True)
        self.assertEqual(self.charge_types.active, "Long_Life")
        self.assertTrue(battery.get_conservation())

    def test_unsupported_rapid_raises_before_writing(self):
        unsupported = FakeChargeTypes(active="Standard", available=("Standard", "Long_Life"))
        with patch.object(battery, "get_charge_types_path", return_value=unsupported):
            with self.assertRaises(ValueError):
                battery.set_charge_mode("fast")
        self.assertEqual(unsupported.active, "Standard")

    def test_disabling_conservation_does_not_clear_rapid(self):
        self.charge_types.active = "Fast"
        battery.set_conservation(False)
        self.assertEqual(battery.get_charge_mode(), "fast")

    def test_disabling_rapid_does_not_clear_conservation(self):
        self.charge_types.active = "Long_Life"
        battery.set_rapid_charge(False)
        self.assertEqual(battery.get_charge_mode(), "long_life")


if __name__ == "__main__":
    unittest.main()
