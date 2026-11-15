#!/usr/bin/env python3
"""Unit tests for power-profile synchronization."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daemon"))

from features import power  # noqa: E402


class PowerModeTests(unittest.TestCase):
    def test_get_power_mode_prefers_power_profiles_daemon(self):
        result = MagicMock(stdout="power-saver\n")

        with patch.object(power.shutil, "which", return_value="/usr/bin/powerprofilesctl"), \
             patch.object(power.subprocess, "run", return_value=result) as run:
            self.assertEqual(power.get_power_mode(), "Quiet")

        run.assert_called_once_with(
            ["powerprofilesctl", "get"],
            capture_output=True,
            text=True,
            check=True,
        )

    def test_get_power_mode_falls_back_to_platform_profile(self):
        with patch.object(power.shutil, "which", return_value=None), \
             patch.object(power.Path, "exists", return_value=True), \
             patch.object(power.Path, "read_text", return_value="balanced\n"):
            self.assertEqual(power.get_power_mode(), "Balanced")

    def test_set_power_mode_uses_power_profiles_daemon(self):
        with patch.object(power.shutil, "which", return_value="/usr/bin/powerprofilesctl"), \
             patch.object(power.subprocess, "run") as run, \
             patch.object(power.Path, "exists") as exists:
            power.set_power_mode("quiet")

        run.assert_called_once_with(
            ["powerprofilesctl", "set", "power-saver"],
            check=True,
            capture_output=True,
            text=True,
        )
        exists.assert_not_called()

    def test_set_power_mode_falls_back_to_platform_profile(self):
        with patch.object(power.shutil, "which", return_value=None), \
             patch.object(power.Path, "exists", return_value=True), \
             patch.object(power.Path, "write_text") as write:
            power.set_power_mode("performance")

        write.assert_called_once_with("performance")

    def test_set_power_mode_raises_without_a_backend(self):
        with patch.object(power.shutil, "which", return_value=None), \
             patch.object(power.Path, "exists", return_value=False):
            with self.assertRaises(RuntimeError):
                power.set_power_mode("balanced")

    def test_invalid_mode_raises(self):
        with self.assertRaises(ValueError):
            power.set_power_mode("turbo")


if __name__ == "__main__":
    unittest.main()
