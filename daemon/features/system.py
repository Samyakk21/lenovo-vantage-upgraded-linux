import glob
from pathlib import Path

SYSTEM_CONTROL_LABELS = {
    "fn_lock": "Fn Lock",
    "flip_to_start": "Flip To Start",
    "instant_boot": "Instant Boot",
    "usb_charging": "Always-On USB",
}

def get_vpc_path():
    vpc_paths = glob.glob("/sys/bus/platform/devices/VPC2004:*")
    return vpc_paths[0] if vpc_paths else None

def detect_capabilities() -> dict:
    vpc = get_vpc_path()
    controls = {
        name: bool(vpc and Path(f"{vpc}/{name}").exists())
        for name in SYSTEM_CONTROL_LABELS
    }

    available = [label for name, label in SYSTEM_CONTROL_LABELS.items() if controls[name]]
    missing = [label for name, label in SYSTEM_CONTROL_LABELS.items() if not controls[name]]
    supported = any(controls.values())

    if not supported:
        reason = "No supported system controls found on this laptop."
    elif missing:
        reason = f"Available: {', '.join(available)}. Not available: {', '.join(missing)}."
    else:
        reason = "All system controls are available."

    return {
        "supported": supported,
        "partial": supported and bool(missing),
        "reason": reason,
        "controls": controls,
    }

def set_fn_lock(enabled: bool) -> None:
    vpc = get_vpc_path()
    if vpc and Path(f"{vpc}/fn_lock").exists(): Path(f"{vpc}/fn_lock").write_text("0" if enabled else "1")

def get_fn_lock() -> bool:
    vpc = get_vpc_path()
    return Path(f"{vpc}/fn_lock").read_text().strip() == "0" if vpc and Path(f"{vpc}/fn_lock").exists() else False

def set_flip_to_start(enabled: bool) -> None:
    vpc = get_vpc_path()
    if vpc and Path(f"{vpc}/flip_to_start").exists(): Path(f"{vpc}/flip_to_start").write_text("1" if enabled else "0")

def get_flip_to_start() -> bool:
    vpc = get_vpc_path()
    return Path(f"{vpc}/flip_to_start").read_text().strip() == "1" if vpc and Path(f"{vpc}/flip_to_start").exists() else False

def set_instant_boot(enabled: bool) -> None:
    vpc = get_vpc_path()
    if vpc and Path(f"{vpc}/instant_boot").exists(): Path(f"{vpc}/instant_boot").write_text("1" if enabled else "0")

def get_instant_boot() -> bool:
    vpc = get_vpc_path()
    return Path(f"{vpc}/instant_boot").read_text().strip() == "1" if vpc and Path(f"{vpc}/instant_boot").exists() else False
