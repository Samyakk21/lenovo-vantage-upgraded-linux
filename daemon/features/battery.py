"""
Battery charge control for Lenovo IdeaPad laptops.

Modern ideapad_laptop kernels expose the standardized power_supply
"charge_types" attribute:

    /sys/class/power_supply/BAT*/charge_types

For example:  "[Fast] Standard Long_Life"

The active mode is wrapped in brackets.  The kernel translates the writes
into the EC's GBMD/SBMC commands and enforces mutual exclusivity between
Rapid Charge ("Fast") and Conservation Mode ("Long_Life").

Older kernels only expose /sys/bus/platform/devices/VPC2004:*/conservation_mode,
so that interface is kept as a fallback.
"""

import glob
from pathlib import Path

# Canonical daemon mode -> value written to the kernel's charge_types file.
CHARGE_MODE_WRITE = {
    "standard":  "Standard",
    "long_life": "Long_Life",
    "fast":      "Fast",
}

# Canonical daemon mode -> human readable label used by the GUI/CLI.
CHARGE_MODE_LABELS = {
    "standard":  "Normal",
    "long_life": "Conservation",
    "fast":      "Rapid Charge",
}

# Accept the various names used by CLIs and older versions of the app.
CHARGE_MODE_ALIASES = {
    "standard":      "standard",
    "normal":        "standard",
    "long_life":     "long_life",
    "long-life":     "long_life",
    "conservation":  "long_life",
    "fast":          "fast",
    "rapid":         "fast",
    "rapid_charge":  "fast",
    "rapid-charge":  "fast",
}

_MODE_ORDER = ("standard", "long_life", "fast")


def get_vpc_path():
    vpc_paths = glob.glob("/sys/bus/platform/devices/VPC2004:*")
    return vpc_paths[0] if vpc_paths else None


def get_battery_path():
    for bat in ["BAT0", "BAT1", "BATT"]:
        if Path(f"/sys/class/power_supply/{bat}").exists():
            return f"/sys/class/power_supply/{bat}"
    for bat in sorted(glob.glob("/sys/class/power_supply/BAT*")):
        if Path(bat).is_dir():
            return bat
    return None


def normalize_charge_mode(mode: str) -> str:
    """Map a user-facing name such as 'rapid' to the canonical daemon mode."""
    key = str(mode).strip().lower().replace(" ", "_")
    canonical = CHARGE_MODE_ALIASES.get(key)
    if canonical is None:
        allowed = ", ".join(_MODE_ORDER)
        raise ValueError(f"Unknown charge mode '{mode}' (expected one of: {allowed})")
    return canonical


def parse_charge_types(text: str):
    """
    Parse the kernel's charge_types output.

    Returns (available_modes, active_mode).  The active value is the one
    wrapped in brackets, e.g. "[Fast] Standard Long_Life".
    """
    available = []
    active = None

    for token in str(text).split():
        is_active = token.startswith("[") and token.endswith("]")
        name = token.strip("[]").lower()
        if name not in CHARGE_MODE_WRITE:
            continue
        if name not in available:
            available.append(name)
        if is_active:
            active = name

    available.sort(key=_MODE_ORDER.index)
    return available, active


def get_charge_types_path():
    bat = get_battery_path()
    if not bat:
        return None
    path = Path(bat) / "charge_types"
    return path if path.exists() else None


def _legacy_conservation_path():
    vpc = get_vpc_path()
    if not vpc:
        return None
    path = Path(vpc) / "conservation_mode"
    return path if path.exists() else None


def get_available_charge_modes() -> list:
    """Return the canonical modes supported by this laptop, best first."""
    path = get_charge_types_path()
    if path is not None:
        try:
            available, _ = parse_charge_types(path.read_text())
            if available:
                return available
        except OSError:
            pass

    # Legacy kernel: only Normal / Conservation are available.
    if _legacy_conservation_path() is not None:
        return ["standard", "long_life"]

    return []


def get_charge_mode() -> str:
    """Return the current canonical charge mode."""
    path = get_charge_types_path()
    if path is not None:
        try:
            _, active = parse_charge_types(path.read_text())
            if active is not None:
                return active
        except OSError:
            pass

    legacy = _legacy_conservation_path()
    if legacy is not None:
        try:
            return "long_life" if legacy.read_text().strip() == "1" else "standard"
        except OSError:
            pass

    return "standard"


def set_charge_mode(mode: str) -> None:
    """
    Set the charge mode and verify the hardware accepted it.

    The kernel already makes Rapid Charge and Conservation Mode mutually
    exclusive, so this only has to write a single value.
    """
    canonical = normalize_charge_mode(mode)
    available = get_available_charge_modes()

    if not available:
        raise FileNotFoundError("No battery charge control interface found")

    if canonical not in available:
        labels = ", ".join(CHARGE_MODE_LABELS[m] for m in available)
        raise ValueError(
            f"{CHARGE_MODE_LABELS[canonical]} is not supported on this laptop "
            f"(available: {labels})"
        )

    path = get_charge_types_path()
    if path is not None:
        path.write_text(CHARGE_MODE_WRITE[canonical] + "\n")
    else:
        legacy = _legacy_conservation_path()
        if legacy is None:
            raise FileNotFoundError("No battery charge control interface found")
        # The legacy interface only knows Conservation Mode.
        legacy.write_text("1" if canonical == "long_life" else "0")

    actual = get_charge_mode()
    if actual != canonical:
        raise RuntimeError(
            f"Kernel did not accept charge mode '{CHARGE_MODE_LABELS[canonical]}' "
            f"(reported '{CHARGE_MODE_LABELS.get(actual, actual)}')"
        )


def get_conservation() -> bool:
    return get_charge_mode() == "long_life"


def set_conservation(enabled: bool) -> None:
    # Only touch the EC when the requested change is needed.  This avoids
    # clearing Rapid Charge when the user merely turns an already-off
    # Conservation switch off.
    if enabled:
        set_charge_mode("long_life")
    elif get_charge_mode() == "long_life":
        set_charge_mode("standard")


def get_rapid_charge() -> bool:
    return get_charge_mode() == "fast"


def set_rapid_charge(enabled: bool) -> None:
    if enabled:
        set_charge_mode("fast")
    elif get_charge_mode() == "fast":
        set_charge_mode("standard")


def detect_capabilities() -> dict:
    bat = get_battery_path()

    if bat is None:
        return {
            "supported": False,
            "partial": False,
            "reason": "Missing battery device",
            "modes": [],
        }

    modes = get_available_charge_modes()
    if not modes:
        return {
            "supported": False,
            "partial": False,
            "reason": "No charge control interface (ideapad_laptop may be too old)",
            "modes": [],
        }

    labels = ", ".join(CHARGE_MODE_LABELS[m] for m in modes)
    return {
        "supported": True,
        "partial": False,
        "reason": f"Available charge modes: {labels}",
        "modes": modes,
    }


def get_usb_charging() -> bool:
    vpc = get_vpc_path()
    if not vpc:
        return False
    try:
        return Path(f"{vpc}/usb_charging").read_text().strip() == "1"
    except FileNotFoundError:
        return False


def set_usb_charging(enabled: bool) -> None:
    vpc = get_vpc_path()
    if not vpc:
        raise FileNotFoundError("VPC device not found")
    Path(f"{vpc}/usb_charging").write_text("1" if enabled else "0")


def get_battery_info() -> dict:
    bat_path = get_battery_path()
    if not bat_path:
        return {}
    p = Path(bat_path)

    def read_safe(file, default=0, is_int=True):
        try:
            val = (p / file).read_text().strip()
            return int(val) if is_int else val
        except (FileNotFoundError, ValueError):
            return default

    energy_now = read_safe("energy_now") or read_safe("charge_now")
    energy_full = read_safe("energy_full") or read_safe("charge_full")
    energy_design = read_safe("energy_full_design") or read_safe("charge_full_design")

    health = round((energy_full / energy_design * 100), 1) if energy_design and energy_full else 0

    return {
        "capacity":    read_safe("capacity"),
        "status":      read_safe("status", default="Unknown", is_int=False),
        "energy_now":  energy_now,
        "energy_full": energy_full,
        "power_now":   read_safe("power_now"),
        "health":      health
    }
