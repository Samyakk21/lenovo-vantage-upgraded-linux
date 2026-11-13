#!/usr/bin/env bash
#
# Manual hardware test for Rapid Charge support.
#
# Run with root privileges:
#   sudo tests/manual_rapid_charge_test.sh
#
# The script saves the current charge mode, switches to Standard, switches to
# Fast, and always restores the original mode on exit.

set -euo pipefail

BAT="$(ls -d /sys/class/power_supply/BAT* 2>/dev/null | head -n 1)"
if [ -z "$BAT" ]; then
    echo "No battery found under /sys/class/power_supply/BAT*" >&2
    exit 1
fi

if [ ! -f "$BAT/charge_types" ]; then
    echo "$BAT/charge_types does not exist; this kernel does not expose Rapid Charge." >&2
    exit 1
fi

original="$(cat "$BAT/charge_types")"
echo "Battery:     $BAT"
echo "Initial:     $original"

if ! grep -q "Fast" "$BAT/charge_types"; then
    echo "This laptop's EC does not advertise the Fast charge type." >&2
    exit 1
fi

restore() {
    echo "Restoring original charge mode..."
    case "$original" in
        *"[Fast]"*)      echo "Fast"      | tee "$BAT/charge_types" >/dev/null ;;
        *"[Long_Life]"*) echo "Long_Life" | tee "$BAT/charge_types" >/dev/null ;;
        *)               echo "Standard"  | tee "$BAT/charge_types" >/dev/null ;;
    esac
    echo "Restored:    $(cat "$BAT/charge_types")"
}
trap restore EXIT INT TERM

echo
echo "Turning Rapid Charge off (Standard)..."
echo "Standard" | tee "$BAT/charge_types" >/dev/null
cat "$BAT/charge_types"
grep -q '\[Standard\]' "$BAT/charge_types" || {
    echo "FAIL: the kernel did not report Standard." >&2
    exit 1
}

echo
echo "Turning Rapid Charge on (Fast)..."
echo "Fast" | tee "$BAT/charge_types" >/dev/null
cat "$BAT/charge_types"
grep -q '\[Fast\]' "$BAT/charge_types" || {
    echo "FAIL: the kernel did not report Fast." >&2
    exit 1
}

echo
echo "PASS: charge_types accepted both Standard and Fast."
