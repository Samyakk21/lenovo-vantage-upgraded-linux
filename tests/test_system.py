#!/usr/bin/env python3
"""Unit tests for VPC2004 system-control capability detection."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daemon"))

from features import system  # noqa: E402
from ipc import dbus_service  # noqa: E402


class SystemCapabilityTests(unittest.TestCase):
    def detect(self, *files):
        with tempfile.TemporaryDirectory() as tmp:
            for name in files:
                Path(tmp, name).touch()
            with patch.object(system, "get_vpc_path", return_value=tmp):
                return system.detect_capabilities()

    def test_flip_to_start_is_detected_on_its_own(self):
        caps = self.detect("flip_to_start")

        self.assertTrue(caps["supported"])
        self.assertTrue(caps["partial"])
        self.assertTrue(caps["controls"]["flip_to_start"])
        self.assertFalse(caps["controls"]["fn_lock"])
        self.assertFalse(caps["controls"]["instant_boot"])
        self.assertFalse(caps["controls"]["usb_charging"])

    def test_all_controls_are_supported(self):
        caps = self.detect("fn_lock", "flip_to_start", "instant_boot", "usb_charging")

        self.assertTrue(caps["supported"])
        self.assertFalse(caps["partial"])
        self.assertTrue(all(caps["controls"].values()))

    def test_no_controls_is_not_partial(self):
        caps = self.detect()

        self.assertFalse(caps["supported"])
        self.assertFalse(caps["partial"])
        self.assertFalse(any(caps["controls"].values()))

    def test_missing_vpc_path_is_not_supported(self):
        with patch.object(system, "get_vpc_path", return_value=None):
            caps = system.detect_capabilities()

        self.assertFalse(caps["supported"])
        self.assertFalse(caps["partial"])

    def test_missing_control_is_explained(self):
        caps = self.detect("fn_lock")

        self.assertTrue(caps["supported"])
        self.assertTrue(caps["partial"])
        self.assertIn("Fn Lock", caps["reason"])
        self.assertIn("Flip To Start", caps["reason"])


class CapabilityPayloadTests(unittest.TestCase):
    def test_system_controls_are_exposed_individually(self):
        fake = {
            "supported": True,
            "partial": True,
            "reason": "test",
            "controls": {
                "fn_lock": True,
                "flip_to_start": False,
                "instant_boot": False,
                "usb_charging": False,
            },
        }

        with patch.object(system, "detect_capabilities", return_value=fake):
            caps = dbus_service.VantageService.GetAllCapabilities(object())

        self.assertTrue(bool(caps["fn_lock"]["supported"]))
        self.assertFalse(bool(caps["flip_to_start"]["supported"]))
        self.assertFalse(bool(caps["instant_boot"]["supported"]))
        self.assertFalse(bool(caps["usb_charging"]["supported"]))
        self.assertIn("Flip To Start", str(caps["flip_to_start"]["reason"]))
