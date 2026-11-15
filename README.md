# Lenovo Vantage Upgraded Linux

Hey! This is an unofficial, community-made Linux control app for Lenovo
laptops. It started as a fork of
[nightcodex7/lenovo-vantage-unofficial-linux](https://github.com/nightcodex7/lenovo-vantage-unofficial-linux)
and builds on the original
[niizam/vantage](https://github.com/niizam/vantage) project.

The main thing this fork adds is a real **Rapid Charge** switch next to
**Conservation Mode**. It uses the kernel's standard `charge_types` interface,
so you don't need `acpi_call`, a DKMS module, or Secure Boot changes just to get
Rapid Charge working.

If you're here because Lenovo Vantage doesn't exist on Linux, you're in the
right place. There's a GUI, a CLI, and a zenity fallback for the common Lenovo
laptop controls.

## Contents

- [Status](#status)
- [What this fork adds](#what-this-fork-adds)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Battery charge modes](#battery-charge-modes)
- [How it works](#how-it-works)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Reporting bugs and hardware results](#reporting-bugs-and-hardware-results)
- [Acknowledgements](#acknowledgements)
- [License](#license)
- [Maintainer](#maintainer)
- [Note](#note)

## Status

I've mainly tested this on a Lenovo IdeaPad Gaming 3 15ACH6 (`82K2`), BIOS
`H3CN32WW(V2.02)`, running Ubuntu 24.04 with kernel 7.0. It should work on many
IdeaPad and Legion laptops that expose the usual `ideapad_laptop`, `VPC2004`,
and power-supply sysfs files, but I haven't tested every model.

If a control shows up as disabled, that usually means the app couldn't find the
interface on your machine. Detection is helpful, but it isn't a promise that
every write will behave the same on every BIOS or firmware version.

Dual-boot note: I haven't fully tested whether the charge mode survives
switching between Windows and Linux. Lenovo firmware or Windows tools can
change it on their own, so check the mode after you switch.

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
- **No** `acpi_call`, DKMS module, or Secure Boot changes required for Rapid
  Charge.

## Features

Here's the stuff you can control:

- **Battery:** Normal, Conservation (`Long_Life`), and Rapid Charge (`Fast`)
  modes, plus battery status and health info.
- **Power profiles:** Quiet, Balanced, and Performance through
  `power-profiles-daemon` and `platform_profile`. The app reads the same source
  as Ubuntu's built-in power mode and refreshes when it changes.
- **Fan modes:** Standard, Super Silent, Dust Cleaning, and Performance through
  `VPC2004:*/fan_mode`.
- **System controls:** Always-On USB, Fn lock, Flip-to-Start, and Instant Boot.
  Each control is detected separately, so a missing sysfs file only disables
  that one row.
- **GPU switching:** Hybrid, Integrated, and Dedicated modes through
  `supergfxctl` or `optimus-manager`.
- **Optional tuning:** RyzenAdj TDP limits, NVIDIA clock offsets, and OpenRGB
  lighting.
- **Sensors:** Temperature, fan, battery, and related telemetry.
- **Three frontends:** PyQt6 GUI, command-line client, and zenity fallback.
- **Capability-aware UI:** Unsupported controls are disabled with a reason
  instead of being silently written.

## Requirements

You'll need:

- Linux with systemd and D-Bus.
- A Lenovo laptop with the right `ideapad_laptop`/`VPC2004` sysfs controls.
- Python 3.10 or newer.
- PyQt6, `dbus-python`, and PyGObject for the GUI and daemon.
- `zenity` and `xinput` for the fallback and some input-related features.
- Root access for installation and for the daemon.

Optional extras:

| Tool | Used for |
|---|---|
| `powerprofilesctl` | Keeping power profiles in sync with power-profiles-daemon |
| `ryzenadj` | Ryzen TDP limits |
| `supergfxctl` or `optimus-manager` | GPU mode switching |
| `openrgb` | RGB lighting control |
| `nvidia-settings` | NVIDIA GPU clock offsets (X11 with Coolbits) |

`install.sh` installs the core Python, Qt, D-Bus, zenity, and input packages on
Arch, Debian/Ubuntu, Fedora, and openSUSE. The optional tools aren't installed
automatically.

## Installation

The short version:

```bash
git clone https://github.com/Samyakk21/lenovo-vantage-upgraded-linux.git
cd lenovo-vantage-upgraded-linux

make test
sudo make install
```

`make install` handles the boring parts for you:

- Installs runtime dependencies through `install.sh`.
- Installs the daemon under `/usr/lib/vantage/daemon/`.
- Installs `vantage-gui`, `vantage-cli`, and the `vantage` zenity fallback.
- Installs the desktop entry, icon, D-Bus policy, and systemd unit.
- Enables and restarts `vantaged.service`.

Check that the service is happy:

```bash
systemctl status vantaged.service
```

If you ever want to remove it:

```bash
sudo make uninstall
```

There's also a manual hardware test that writes to the real EC and then
restores the original mode:

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

The GUI has Dashboard, Power, Battery, Actions, Settings, and About pages.
Battery controls are disabled with an explanation when the daemon or hardware
doesn't support them.

### CLI

The CLI is handy for scripts or when you don't want to open the GUI:

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

Want JSON? It's supported too:

```bash
vantage-cli --json capabilities
vantage-cli --json battery
vantage-cli --json sensors
```

`battery on` and `battery off` are legacy aliases for Conservation Mode and
Normal mode. For clarity, I'd stick with `battery conservation`,
`battery rapid`, and `battery normal`.

### Zenity fallback

```bash
vantage
```

The fallback gives you a menu for the most common controls and uses `pkexec`
for privileged writes. It's handy on systems without PyQt6 or when the daemon
isn't running.

## Battery charge modes

This is the part most people come here for.

Modern `ideapad_laptop` kernels expose the battery charge modes at:

```text
/sys/class/power_supply/BAT*/charge_types
```

Example output:

```text
[Fast] Standard Long_Life
```

The value in brackets is the currently active mode.

| Mode | Kernel value | What it does |
|---|---|---|
| Normal | `Standard` | Rapid Charge and Conservation are off |
| Conservation | `Long_Life` | Caps charging below 100% (usually around 55-60%, depending on your model and firmware) |
| Rapid Charge | `Fast` | Charges quickly, usually reaching 80% fast before continuing to 100% |

Conservation Mode and Rapid Charge are **mutually exclusive**. The kernel/EC
keeps one active charge mode at a time, and the GUI refreshes both switches
after every write so the UI matches the hardware.

Toggling a switch that's already off does nothing. For example, turning off
Conservation Mode doesn't clear Rapid Charge, and turning off Rapid Charge
doesn't turn on Conservation Mode. Use `battery normal` or set the mode you
actually want.

On older kernels where `charge_types` doesn't exist, the daemon falls back to
`VPC2004:*/conservation_mode`. That interface only supports Normal and
Conservation, so Rapid Charge shows up as unsupported.

## How it works

Under the hood, the GUI and CLI don't write hardware directly. They talk to a
small root-owned D-Bus daemon, which does the capability checks and writes the
sysfs files. The GUI has one read-only sysfs fallback to detect per-control
support when it's running against an older daemon.

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

Useful details:

- **D-Bus bus name:** `org.lenovo.Vantage`
- **Object path:** `/org/lenovo/Vantage`
- **Interface:** `org.lenovo.Vantage`
- **Service unit:** `vantaged.service`
- **Daemon install path:** `/usr/lib/vantage/daemon/vantaged.py`

Power profiles prefer `powerprofilesctl`, so changes stay in sync with Ubuntu's
built-in power mode. Direct `platform_profile` writes are used only when
power-profiles-daemon isn't available.

The GUI also polls the daemon about once a second for the quick controls. That
means changes made with hardware hotkeys (such as Fn+Q for power mode or Fn+Esc
for Fn Lock), the CLI, or another app show up without restarting the GUI. GPU
mode is checked less often because changing it needs a reboot. The live
refresh leaves the TDP fields alone, and a dropdown is skipped while it's open
so the refresh doesn't fight your selection.

The zenity fallback (`/usr/bin/vantage`) is a standalone shell script. It uses
`pkexec` to write the same sysfs interfaces and doesn't need the daemon.

## Troubleshooting

If something isn't working, start here.

### The GUI or CLI can't connect to the daemon

```bash
systemctl status vantaged.service
journalctl -u vantaged.service -b --no-pager
```

If the service isn't installed, run `sudo make install`. If it's failing, check
that `dbus-python`, `PyGObject`, and Python 3.10+ are installed.

### Rapid Charge is disabled

Check what your EC says:

```bash
cat /sys/class/power_supply/BAT*/charge_types
```

- No `Fast` entry? Your laptop's EC doesn't support Rapid Charge through this
  kernel interface.
- The file is missing? The kernel only supports the older Conservation Mode
  fallback.
- `Fast` is there but the switch is still disabled? Make sure the new daemon is
  installed and `vantaged.service` has been restarted. An older daemon doesn't
  know about the Rapid Charge D-Bus methods.

### All controls are disabled

Run:

```bash
vantage-cli capabilities
```

That tells you which features were detected and why unsupported ones are
disabled. Check that the expected sysfs paths exist and that the daemon is
running.

### Flip To Start or Instant Boot is disabled

These controls need their own `VPC2004` sysfs files (`flip_to_start`,
`instant_boot`, and `usb_charging`). If your model doesn't expose one of them,
that row is disabled even when Fn Lock works. This is expected. If the controls
worked before an upgrade, restart the updated `vantaged.service`. Newer daemons
report each control separately, while the GUI falls back to a read-only sysfs
check with older ones.

### Permission errors

Run the GUI and CLI as your normal user, not with `sudo` or as root. The
root-owned daemon does the privileged writes. Running a frontend as root can
also cause D-Bus session and display weirdness.

### The charge mode resets after reboot or after using Windows

Firmware, BIOS updates, or Lenovo software on another OS can change the mode.
Just set it again after booting. Dual-boot persistence isn't guaranteed, and I
haven't fully tested it.

### A feature works, but not the way you expected

Stop using that control and report your model, BIOS version, kernel version, and
the sysfs values. Some features depend on undocumented firmware behavior and
may need model-specific handling.

## Development

Want to poke around or add a feature? Here's the layout.

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

Stop the installed daemon first if it's running, then start the source daemon:

```bash
sudo systemctl stop vantaged.service
sudo python3 daemon/vantaged.py
```

In another terminal:

```bash
python3 cli/vantage-cli.py capabilities
python3 cli/vantage-gui.py
```

The daemon needs root because it writes root-owned sysfs attributes.

### Tests

```bash
make test
```

The unit tests cover charge-mode parsing, validation, writes, read-back
verification, legacy fallback, and capability detection. They don't touch real
hardware.

The manual hardware test does write to the EC, and it restores the original
mode when it's done:

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

There are more methods for power, fan, GPU, system, sensors, RGB, overclock,
and automation in `daemon/ipc/dbus_service.py`.

When you add a control:

1. Add capability detection in the relevant `daemon/features/*.py` module.
2. Validate inputs against a fixed allowlist. Don't expose arbitrary sysfs or
   ACPI writes through D-Bus.
3. Read the value back where possible so you can verify the write.
4. Expose it through the daemon, then add CLI and GUI support.
5. Add unit tests with mocked sysfs paths.

### Style

The repo includes an `.editorconfig`: UTF-8, LF line endings, trimmed trailing
whitespace, 4-space Python and shell indentation, and literal tabs in the
Makefile. Keep hardware access in `daemon/features/` for the daemon, GUI, and
CLI path rather than in the frontends. The zenity fallback is the legacy
exception.

## Reporting bugs and hardware results

Found a bug? Want to share your hardware results? Open an issue on
[GitHub](https://github.com/Samyakk21/lenovo-vantage-upgraded-linux/issues).

Hardware reports are especially useful if you have a Lenovo system that isn't
listed yet. Please include:

```bash
cat /sys/class/dmi/id/product_name
cat /sys/class/dmi/id/product_version
cat /sys/class/dmi/id/bios_version
uname -r
cat /sys/class/power_supply/BAT*/charge_types
vantage-cli --json capabilities
journalctl -u vantaged.service -b --no-pager
```

Also tell me which control failed, what you expected, and what actually
happened. Please don't include sensitive personal information.

## Acknowledgements

Big thanks to:

- [nightcodex7/lenovo-vantage-unofficial-linux](https://github.com/nightcodex7/lenovo-vantage-unofficial-linux)
  — the direct upstream base for the daemon, GUI, CLI, and zenity frontend.
- [niizam/vantage](https://github.com/niizam/vantage)
  — the original unofficial Lenovo Vantage implementation for Linux, which
  provided the foundation for controls like Conservation Mode, Fan Mode, and
  Fn Lock.
- [LenovoLegionToolkit](https://github.com/BartoszCichecki/LenovoLegionToolkit)
  — inspiration for the Windows feature set.

Both upstream projects are licensed under GNU GPL-3.0.

Modifications in this fork include Rapid Charge support, charge-mode
capability detection, ACPI/sysfs interface handling, GUI/CLI/zenity
integration, tests, and documentation updates.

## License

GNU General Public License v3.0. See [LICENSE](LICENSE) for the full text.

Lenovo is a trademark of Lenovo Group Ltd. This project isn't affiliated with
Lenovo.

## Maintainer

Maintained by [@Samyakk21](https://github.com/Samyakk21). Questions, bugs, and
suggestions are welcome via GitHub issues. If you have a Lenovo system, please
consider sharing what works and what doesn't so support can improve.

## Note

A friendly but important note: this project is unofficial and not affiliated
with Lenovo. I've tested it on my IdeaPad Gaming 3 15ACH6, but not on every
Lenovo laptop out there. Features may work differently on your machine, and
some may not work at all or may give results you don't expect.

Some controls write to kernel sysfs interfaces handled by the Lenovo EC. Please
use common sense, back up anything important, and understand what you're
changing before you change it.

I can't guarantee compatibility, and to the extent the law allows, I can't be
held liable for any damage, data loss, hardware failure, voided warranty, or
other issues that come from using this software. You're responsible for the
changes you make to your system. If that sounds like too much risk, please
don't use it.
