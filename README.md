# Lenovo Vantage Upgraded

A GPL-3.0 Linux toolkit for Lenovo laptops, forked from
[nightcodex7/lenovo-vantage-unofficial-linux](https://github.com/nightcodex7/lenovo-vantage-unofficial-linux).
It adds **Rapid Charge** support alongside the original Conservation Mode,
power, fan, USB, Fn-lock and GPU controls.

Tested on an **IdeaPad Gaming 3 15ACH6 (82K2)** running Ubuntu 24.04 with
kernel 7.0. Other Lenovo models may work depending on the `ideapad_laptop`
driver and EC firmware.

## Features

- **Battery charge modes:** Normal, Conservation (`Long_Life`) and Rapid Charge (`Fast`)
- **Power and thermals:** power profiles, fan modes and optional RyzenAdj TDP tuning
- **System controls:** Always-On USB, Fn lock, Flip-to-Start and Instant Boot
- **GPU switching:** Hybrid, Integrated and Dedicated modes through `supergfxctl`
- **Three frontends:** PyQt6 GUI, command-line client and zenity fallback
- **Capability detection:** unsupported controls are disabled with a reason
- **No extra kernel modules:** Rapid Charge uses the standard `charge_types`
  power-supply interface, so no `acpi_call`, DKMS module or Secure Boot change
  is required

## Battery modes

Modern `ideapad_laptop` kernels expose the charge modes at
`/sys/class/power_supply/BAT*/charge_types`:

```text
[Fast] Standard Long_Life
```

| Mode | Kernel value | Effect |
|---|---|---|
| Normal | `Standard` | Rapid Charge and Conservation off |
| Conservation | `Long_Life` | Caps charging at 60-80% |
| Rapid Charge | `Fast` | Charges faster to 100% |

Conservation Mode and Rapid Charge are mutually exclusive. The EC enforces
this, and the GUI refreshes both switches after every change. On older kernels
the app falls back to `VPC2004:*/conservation_mode`, which supports Normal and
Conservation only.

## Installation

`install.sh` installs the required packages on Arch, Debian/Ubuntu, Fedora and
openSUSE. `ryzenadj` is optional and only needed for TDP control.

```bash
git clone https://github.com/Samyakk21/lenovo-vantage-upgraded.git
cd lenovo-vantage-upgraded

make test
sudo make install
```

`make install` installs the daemon, GUI, CLI, zenity fallback, D-Bus policy and
systemd service, then restarts `vantaged.service`.

To verify the real EC write path (the script restores the original mode):

```bash
sudo tests/manual_rapid_charge_test.sh
```

## Usage

```bash
vantage-gui                      # PyQt6 GUI
vantage                          # zenity fallback

vantage-cli battery              # print the current charge mode
vantage-cli battery normal
vantage-cli battery conservation
vantage-cli battery rapid
vantage-cli rapid on
vantage-cli rapid off
```

All CLI commands accept `--json`.

If the Rapid Charge switch is disabled, check what the EC advertises:

```bash
cat /sys/class/power_supply/BAT*/charge_types
```

No `Fast` entry means the laptop's EC does not support Rapid Charge. A missing
file means the kernel only supports Conservation Mode.

## Project layout

- `daemon/` — root D-Bus daemon and hardware backends
- `cli/` — PyQt6 GUI and command-line client
- `vantage.sh` — zenity fallback
- `dbus/` and `systemd/` — service integration
- `tests/` — backend tests and manual hardware test

## Acknowledgements

This project builds upon:

- [nightcodex7/lenovo-vantage-unofficial-linux](https://github.com/nightcodex7/lenovo-vantage-unofficial-linux)
  — the direct upstream base for the daemon, GUI, CLI and zenity frontend.
- [niizam/vantage](https://github.com/niizam/vantage)
  — the original unofficial Lenovo Vantage implementation for Linux, which
  provided the foundation for controls such as Conservation Mode, Fan Mode
  and Fn Lock.
- [LenovoLegionToolkit](https://github.com/BartoszCichecki/LenovoLegionToolkit)
  — inspiration for the Windows feature set.

Both upstream projects are licensed under GNU GPL-3.0.

Modifications in this fork include Rapid Charge support, charge-mode
capability detection, ACPI/sysfs interface handling, GUI/CLI/zenity
integration, tests and documentation updates.

## License

GNU General Public License v3.0. See [LICENSE](LICENSE).
