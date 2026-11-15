# Lenovo Vantage Upgraded Linux Changelog

## Unreleased

- Renamed the project and repository to **Lenovo Vantage Upgraded Linux**.
- Expanded the README with architecture, development, troubleshooting, and
  hardware-reporting guidance.
- Added a friendlier compatibility and liability note at the end of the README.
- Power modes now use power-profiles-daemon as the source of truth when it is
  available, and the GUI refreshes when Ubuntu's built-in mode changes.
- Fixed Flip To Start, Instant Boot, and Always-On USB detection so each
  control is enabled or disabled independently.

## 1.1.0 - Rapid Charge release

- Renamed the project to **Lenovo Vantage Upgraded** to match the repository.
- Added GPL-3.0 copyright notices and upstream acknowledgements.
- Rewrote the README with concise install, usage and compatibility notes.
- Added Rapid Charge (`Fast`) support through the kernel's standard
  `charge_types` power-supply attribute.
- Replaced the Battery page's Normal/Conservation combo with two mutually
  exclusive switches: **Conservation Mode** and **Rapid Charge**. The GUI
  refreshes both from the hardware after every change.
- Added D-Bus methods: `GetChargeMode`, `SetChargeMode`,
  `GetAvailableChargeModes`, `GetRapidCharge`, and `SetRapidCharge`.
- Added CLI commands: `vantage-cli rapid [on|off]` and
  `vantage-cli battery [normal|conservation|rapid]`.
- Added Rapid Charge to the zenity fallback menu.
- Kept `VPC2004:*/conservation_mode` as a fallback for older kernels.
- Added unit tests and a manual hardware write test.
- No new installer dependencies. `acpi_call`, DKMS, and Secure Boot changes
  are not required.
