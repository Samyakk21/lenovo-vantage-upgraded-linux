# Lenovo Vantage Upgraded Linux

An unofficial, community-maintained Linux control suite for Lenovo laptops,
forked from
[nightcodex7/lenovo-vantage-unofficial-linux](https://github.com/nightcodex7/lenovo-vantage-unofficial-linux)
and built on the original
[niizam/vantage](https://github.com/niizam/vantage) project.

The main addition in this fork is a real **Rapid Charge** switch alongside
**Conservation Mode**, implemented through the kernel's standard
`charge_types` power-supply interface.

> [!WARNING]
> **This is unofficial software. Use it at your own risk.**
>
> This project is not affiliated with, endorsed by, or supported by Lenovo.
> It has been tested on the hardware listed below, but **not on all machines**.
> Features may not work, may behave differently, or may produce undesirable
> results on your laptop, BIOS, kernel, or firmware. Some controls write to
> kernel sysfs interfaces handled by the Lenovo embedded controller (EC).
>
> To the maximum extent permitted by applicable law, the author and
> contributors **cannot be held liable** for any damage, data loss, hardware
> failure, voided warranty, or other consequences resulting from the use of
> this software. Back up important data before changing hardware settings.

## Contents

- [Status](#status)
- [What this fork adds](#what-this-fork-adds)
- [Features](#features)
- [Battery charge modes](#battery-charge-modes)
- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Reporting bugs and hardware results](#reporting-bugs-and-hardware-results)
- [Acknowledgements](#acknowledgements)
- [License](#license)
- [Maintainer](#maintainer)
- [Safety and liability](#safety-and-liability)

## Status

- **Primary test machine:** Lenovo IdeaPad Gaming 3 15ACH6 (`82K2`), BIOS
  `H3CN32WW(V2.02)`, Ubuntu 24.04, kernel 7.0.
- **Expected to work:** Many Lenovo IdeaPad and Legion laptops that expose the
  relevant `ideapad_laptop`, `VPC2004`, and power-supply sysfs interfaces.
- **Not tested on all machines.** Some features are model-, BIOS-, kernel-, or
  firmware-dependent. The GUI disables controls that are not detected, but
  detection is not a guarantee that a write will behave as expected.
- **Dual-boot note:** Charge-mode persistence across Windows and Linux has not
  been fully tested. Lenovo firmware or Windows tools may change the setting
  independently. Check the mode after switching operating systems.

## What this fork adds

Compared with the upstream projects, this fork adds:

- **Rapid Charge support** using `/sys/class/power_supply/BAT*/charge_types`.
- Two mutually exclusive battery switches in the GUI: **Conservation Mode** and
  **Rapid Charge**.
- D-Bus methods for reading and writing the full charge mode.
- `vantage-cli rapid` and an expanded `vantage-cli battery` command.
- Rapid Charge in the zenity fallback menu.
- Capability detection and read-back verification before reporting success.
- Unit tests and a manual hardware write test.
- **No** `acpi_call`, DKMS module, or Secure Boot changes are required for
  Rapid Charge.

## Features

- **Battery control:** Normal, Conservation (`Long_Life`), and Rapid Charge
  (`Fast`) modes, plus battery status and health information.
- **Power profiles:** Quiet, Balanced, and Performance through
  `platform_profile` and, when available, `power-profiles-daemon`.
- **Fan modes:** Standard, Super Silent, Dust Cleaning, and Performance through
  `VPC2004:*/fan_mode`.
- **System controls:** Always-On USB, Fn lock, Flip-to-Start, and Instant Boot.
- **GPU switching:** Hybrid, Integrated, and Dedicated modes through
  `supergfxctl` or `optimus-manager`.
- **Optional tuning:** RyzenAdj TDP limits, NVIDIA clock offsets, and OpenRGB
  lighting.
- **Sensors:** Temperature, fan, battery, and related telemetry.
- **Three frontends:** PyQt6 GUI, command-line client, and zenity fallback.
- **Capability-aware UI:** Unsupported controls are disabled with a reason
  instead of being silently written.

## Battery charge modes

Modern `ideapad_laptop` kernels expose the battery charge modes at:

```text
/sys/class/power_supply/BAT*/charge_types
```

Example output:

```text
[Fast] Standard Long_Life
```

The value in brackets is the currently active mode.

| Mode | Kernel value | Effect |
|---|---|---|
| Normal | `Standard` | Rapid Charge and Conservation are off |
| Conservation | `Long_Life` | Caps charging below 100% (typically around 55-60%, depending on model and firmware) |
| Rapid Charge | `Fast` | Prioritizes fast charging, typically reaching 80% quickly before continuing to 100% |

Conservation Mode and Rapid Charge are **mutually exclusive**. The
kernel/EC exposes a single active charge mode, and the GUI refreshes both
switches after every write so the UI reflects the hardware.

Toggling an already-off switch is a no-op. For example, disabling Conservation
Mode does not clear Rapid Charge, and disabling Rapid Charge does not enable
Conservation Mode. Use `battery normal` or set the desired mode explicitly.

On older kernels where `charge_types` is unavailable, the daemon falls back to
`VPC2004:*/conservation_mode`. That interface supports Normal and Conservation
only, so Rapid Charge is reported as unsupported.

## How it works

The GUI and CLI do not write hardware interfaces directly. They talk to a
root-owned D-Bus daemon, which performs capability checks and writes the
relevant sysfs attributes.

```text
vantage-gui / vantage-cli
        |
        | D-Bus system bus (org.lenovo.Vantage)
        v
vantaged (root daemon)
        |
        +-- daemon/features/battery.py  -> /sys/class/power_supply/BAT*/charge_types
        +-- daemon/features/fan.py      -> VPC2004:*/fan_mode
        +-- daemon/features/power.py    -> /sys/firmware/acpi/platform_profile
        +-- daemon/features/system.py   -> VPC2004:*/fn_lock, usb_charging, ...
        +-- daemon/features/gpu.py      -> supergfxctl / optimus-manager
```

- **D-Bus bus name:** `org.lenovo.Vantage`
- **Object path:** `/org/lenovo/Vantage`
- **Interface:** `org.lenovo.Vantage`
- **Service unit:** `vantaged.service`
- **Daemon install path:** `/usr/lib/vantage/daemon/vantaged.py`

The zenity fallback (`/usr/bin/vantage`) is a standalone shell script. It uses
`pkexec` to write the same sysfs interfaces and does not require the daemon.

## Requirements

- Linux with systemd and D-Bus.
- A Lenovo laptop with the relevant `ideapad_laptop`/`VPC2004` sysfs controls.
- Python 3.10 or newer.
- PyQt6, `dbus-python`, and PyGObject for the GUI and daemon.
- `zenity` and `xinput` for the fallback and some input-related features.
- Root access for installation and for the daemon.

Optional external tools:

| Tool | Used for |
|---|---|
| `powerprofilesctl` | Keeping power profiles in sync with power-profiles-daemon |
| `ryzenadj` | Ryzen TDP limits |
| `supergfxctl` or `optimus-manager` | GPU mode switching |
| `openrgb` | RGB lighting control |
| `nvidia-settings` | NVIDIA GPU clock offsets (X11 with Coolbits) |

`install.sh` installs the core Python, Qt, D-Bus, zenity, and input packages on
Arch, Debian/Ubuntu, Fedora, and openSUSE. Optional tools are not installed
automatically.

## Installation

```bash
git clone https://github.com/Samyakk21/lenovo-vantage-upgraded-linux.git
cd lenovo-vantage-upgraded-linux

make test
sudo make install
```

`make install`:

- Installs runtime dependencies through `install.sh`.
- Installs the daemon under `/usr/lib/vantage/daemon/`.
- Installs `vantage-gui`, `vantage-cli`, and the `vantage` zenity fallback.
- Installs the desktop entry, icon, D-Bus policy, and systemd unit.
- Enables and restarts `vantaged.service`.

Verify the service:

```bash
systemctl status vantaged.service
```

To uninstall:

```bash
sudo make uninstall
```

To test the real EC write path on your machine (the script saves and restores
the original mode):

```bash
sudo tests/manual_rapid_charge_test.sh
```

> If you cloned the old repository URL, update your remote:
>
> ```bash
> git remote set-url origin https://github.com/Samyakk21/lenovo-vantage-upgraded-linux.git
> ```

## Usage

### GUI

```bash
vantage-gui
```

The GUI includes Dashboard, Power, Battery, Actions, Settings, and About pages.
Battery controls are disabled with an explanatory message when the daemon or
hardware does not support them.

### CLI

```bash
vantage-cli capabilities          # show detected hardware support
vantage-cli power                 # print current power mode
vantage-cli power performance     # quiet, balanced, performance
vantage-cli fan                   # print current fan mode
vantage-cli fan super_silent      # standard, super_silent, dust_cleaning, performance
vantage-cli battery               # print current charge mode
vantage-cli battery normal        # standard / normal
vantage-cli battery conservation  # long_life / on
vantage-cli battery rapid         # fast
vantage-cli rapid                 # print Rapid Charge state
vantage-cli rapid on
vantage-cli rapid off
vantage-cli usb on                # Always-On USB
vantage-cli fnlock on
vantage-cli gpu hybrid            # integrated, hybrid, dedicated
vantage-cli sensors
vantage-cli tdp --stapm 45000 --fast 45000 --slow 45000
vantage-cli automation on_ac_connect --power balanced --gpu hybrid
vantage-cli rgb static --color FF0000
vantage-cli overclock 100 200
```

Global JSON output is supported:

```bash
vantage-cli --json capabilities
vantage-cli --json battery
vantage-cli --json sensors
```

`battery on` and `battery off` are legacy aliases for Conservation Mode and
Normal mode. For clarity, prefer `battery conservation`, `battery rapid`, and
`battery normal`.

### Zenity fallback

```bash
vantage
```

The fallback provides a menu for the most common controls and uses `pkexec`
for privileged writes. It is useful on systems without PyQt6 or when the
daemon is not running.

## Troubleshooting

### The GUI or CLI cannot connect to the daemon

```bash
systemctl status vantaged.service
journalctl -u vantaged.service -b --no-pager
```

If the service is not installed, run `sudo make install`. If it is failing,
check that `dbus-python`, `PyGObject`, and Python 3.10+ are installed.

### Rapid Charge is disabled

Check what the EC advertises:

```bash
cat /sys/class/power_supply/BAT*/charge_types
```

- No `Fast` entry: the laptop's EC does not support Rapid Charge through this
  kernel interface.
- Missing file: the kernel only supports the older Conservation Mode fallback.
- `Fast` is present but the switch is still disabled: make sure the new daemon
  is installed and `vantaged.service` has been restarted. An older daemon does
  not expose the Rapid Charge D-Bus methods.

### All controls are disabled

Run:

```bash
vantage-cli capabilities
```

The output shows which features were detected and why unsupported features are
disabled. Check that the expected sysfs paths exist and that the daemon is
running.

### Permission errors

The GUI and CLI should be run as your normal user, not with `sudo` or as root.
The root-owned daemon performs the privileged writes. If you run a frontend as
root, D-Bus session and display behavior may be incorrect.

### The charge mode resets after reboot or after using Windows

Firmware, BIOS updates, or Lenovo software on another OS may change the mode.
Reapply the desired mode after booting. Dual-boot persistence is not guaranteed
and has not been fully tested.

### A feature works but behaves unexpectedly

Stop using that control and report the model, BIOS version, kernel version, and
the sysfs values. Some features depend on undocumented firmware behavior and
may need model-specific handling.

## Development

### Project layout

| Path | Purpose |
|---|---|
| `daemon/vantaged.py` | Root daemon entry point and D-Bus main loop |
| `daemon/ipc/dbus_service.py` | D-Bus API exposed to frontends |
| `daemon/features/` | Hardware backends and capability detection |
| `daemon/features/battery.py` | Charge-mode parsing, validation, writes, and fallback |
| `cli/vantage-gui.py` | PyQt6 GUI |
| `cli/vantage-cli.py` | Command-line client |
| `vantage.sh` | Zenity fallback |
| `dbus/` | D-Bus policy |
| `systemd/` | `vantaged.service` unit |
| `tests/` | Backend unit tests and manual hardware test |
| `install.sh` | Distribution dependency detection and installation |

### Running from source

Stop the installed daemon first if it is running, then start the source daemon:

```bash
sudo systemctl stop vantaged.service
sudo python3 daemon/vantaged.py
```

In another terminal:

```bash
python3 cli/vantage-cli.py capabilities
python3 cli/vantage-gui.py
```

The daemon must run as root because it writes root-owned sysfs attributes.

### Tests

```bash
make test
```

The unit tests cover charge-mode parsing, validation, writes, read-back
verification, legacy fallback, and capability detection. They do not write to
real hardware.

The manual hardware test does write to the EC and restores the original mode:

```bash
sudo tests/manual_rapid_charge_test.sh
```

### D-Bus API

Battery-related methods:

| Method | Signature | Purpose |
|---|---|---|
| `GetChargeMode` | `() -> s` | Return `standard`, `long_life`, or `fast` |
| `SetChargeMode` | `(s) -> ()` | Set one of the validated charge modes |
| `GetAvailableChargeModes` | `() -> as` | Return the modes supported by the EC |
| `GetConservation` | `() -> b` | Compatibility wrapper for Conservation Mode |
| `SetConservation` | `(b) -> ()` | Compatibility wrapper for Conservation Mode |
| `GetRapidCharge` | `() -> b` | Return whether Rapid Charge is active |
| `SetRapidCharge` | `(b) -> ()` | Enable or disable Rapid Charge |
| `GetAllCapabilities` | `() -> a{sa{sv}}` | Report support, partial support, reason, and modes |

See `daemon/ipc/dbus_service.py` for power, fan, GPU, system, sensor, RGB,
overclock, and automation methods.

When adding a control:

1. Add capability detection in the relevant `daemon/features/*.py` module.
2. Validate inputs against a fixed allowlist. Do not expose arbitrary sysfs or
   ACPI writes through D-Bus.
3. Verify the write by reading the value back where possible.
4. Expose it through the daemon, then add CLI and GUI support.
5. Add unit tests with mocked sysfs paths.

### Style

The repository includes an `.editorconfig`: UTF-8, LF line endings, trimmed
trailing whitespace, 4-space Python and shell indentation, and literal tabs in
the Makefile. Keep hardware access in `daemon/features/` for the daemon, GUI,
and CLI path rather than in the frontends. The zenity fallback is the legacy
exception.

## Reporting bugs and hardware results

Questions, bugs, and suggestions are welcome via
[GitHub issues](https://github.com/Samyakk21/lenovo-vantage-upgraded-linux/issues).

If you have a Lenovo system, hardware reports are especially useful. Please
include:

```bash
cat /sys/class/dmi/id/product_name
cat /sys/class/dmi/id/product_version
cat /sys/class/dmi/id/bios_version
uname -r
cat /sys/class/power_supply/BAT*/charge_types
vantage-cli --json capabilities
journalctl -u vantaged.service -b --no-pager
```

Also describe which control failed, what you expected, and what actually
happened. Do not include sensitive personal information.

## Acknowledgements

This project builds upon:

- [nightcodex7/lenovo-vantage-unofficial-linux](https://github.com/nightcodex7/lenovo-vantage-unofficial-linux)
  — the direct upstream base for the daemon, GUI, CLI, and zenity frontend.
- [niizam/vantage](https://github.com/niizam/vantage)
  — the original unofficial Lenovo Vantage implementation for Linux, which
  provided the foundation for controls such as Conservation Mode, Fan Mode,
  and Fn Lock.
- [LenovoLegionToolkit](https://github.com/BartoszCichecki/LenovoLegionToolkit)
  — inspiration for the Windows feature set.

Both upstream projects are licensed under GNU GPL-3.0.

Modifications in this fork include Rapid Charge support, charge-mode
capability detection, ACPI/sysfs interface handling, GUI/CLI/zenity
integration, tests, and documentation updates.

## License

GNU General Public License v3.0. See [LICENSE](LICENSE).

Lenovo is a trademark of Lenovo Group Ltd. This project is not affiliated with
Lenovo.

## Maintainer

Maintained by [@Samyakk21](https://github.com/Samyakk21). Questions, bugs, and
suggestions are welcome via GitHub issues. If you have a Lenovo system, please
consider sharing what works and what does not so support can improve.

## Safety and liability

This software is provided **as is**, without warranty of any kind, express or
implied, including but not limited to the warranties of merchantability,
fitness for a particular purpose, and non-infringement.

It has not been tested on all machines. Compatibility, behavior, and results
may vary by model, BIOS, firmware, kernel, and installed tools. Some features
may not work as intended or may produce undesirable outcomes.

To the maximum extent permitted by applicable law, the author and contributors
**cannot be held liable** for any direct, indirect, incidental, special,
consequential, or exemplary damages, including but not limited to loss of data,
loss of profits, hardware damage, system instability, or voided warranties,
arising from the use of or inability to use this software.

By using this software, you accept these risks and agree that you are
responsible for the changes you make to your system.
