# AGENTS.md: picking up the Fantastic project

Fan detection and control software for Linux (Ubuntu 24.04+ / Pop!_OS). README.md covers usage. This file holds what an agent needs to know to resume work.

## Project rules

- **Python ≥ 3.10, standard library only.** No pip dependency. The GUI uses PyGObject + GTK 4 + libadwaita ≥ 1.5, installed with apt (`python3-gi gir1.2-gtk-4.0 gir1.2-adw-1`). NVML is called through ctypes, not `pynvml`.
- **Language:** code, comments, docstrings, logs and docs are in **English**. User-facing texts are English msgids, translated at display time (see "Translations" below).
- **Never write to real hardware** (`/sys/class/hwmon/*/pwm*`, NVML) without the user's explicit consent. Tests use a simulated sysfs.
- **`sudo`:** the agent cannot type the password. Ask the user to run the command.
- Any new control feature must keep the safety guarantees: back to automatic when the service stops, thermal failsafe, hardware minimums.

## Useful commands

```bash
python3 -m unittest discover -s tests        # tests, no hardware involved
python3 -m fantastic detect                  # real detection, read-only
python3 -m fantastic list -t                 # through the service if it runs, otherwise direct read
# Test service without root (no writes as long as no target is sent):
python3 -m fantastic daemon --socket $XDG_RUNTIME_DIR/f.sock --state $XDG_RUNTIME_DIR/f.json --config /dev/null
FANTASTIC_SOCKET=$XDG_RUNTIME_DIR/f.sock python3 -m fantastic list
FANTASTIC_LANG=de python3 -m fantastic list  # force a language
python3 tools/screenshot.py --lang en        # regenerate docs/screenshot.png (on the host, service running)
```

**User environment:** the agent has sometimes run inside the VS Code Flatpak (`FLATPAK_ID=com.visualstudio.code`), where Python and libraries differ from the host. To run on the host, use `flatpak-spawn --host sh -c '…'`. The user plans to switch to Claude Code in a native terminal.

**Testing the GUI safely:** run a non-root test service on a temporary socket, with a state file that holds only `names` and `hidden` (never `targets`/`originals`, or it would write to the hardware and restore "auto" on exit). Fantastic may already be open on the desktop: scripts must set `Gio.ApplicationFlags.NON_UNIQUE`.

## Architecture

| File | Role |
|---|---|
| `fantastic/hwmon.py` | hwmon chips: `HwmonChip`, `HwmonFan`, `HwmonTemp`, Kraken quirks |
| `fantastic/nvidia.py` | NVML ctypes binding: `Nvml`, `NvidiaGpu`, `NvidiaFan`, `NvidiaTemp` |
| `fantastic/identify.py` | Chip name → (title, kind) table, USB/PCI lookup, DMI, `pci.ids`, CPU model |
| `fantastic/hardware.py` | `Hardware`: unified sorted inventory, `snapshot(lang)`, `local_status(lang)`, `hottest()`, `hints` |
| `fantastic/daemon.py` | `FanService` (targets, state, thermal failsafe, reapplication) and Unix socket server |
| `fantastic/client.py` | Socket `Client` (one JSON line per request); sends the process language with every request |
| `fantastic/cli.py` | `fantastic` entry point (list/set/auto/rename/hide/unhide/detect/gui/daemon) |
| `fantastic/gui.py` | GTK4/Adw. `Worker`: single thread for service calls. `Backend`: read-only fallback without the service. Layout and language menu: see below |
| `fantastic/i18n.py`, `fantastic/translations/*.py` | Translations (see below) |
| `fantastic/fmt.py` | Number formatting per language (separators, units) |
| `data/` | systemd unit, .desktop file (translated), flat-design SVG icon |
| `install.sh` / `uninstall.sh` | Install into `/opt/fantastic` + `/usr/local/bin/fantastic` + service |
| `tests/fakesys.py` | Builds a fake `/sys` (`build_desktop()` mirrors the reference machine) |
| `tests/test_i18n.py` | Checks every msgid of the code is translated in every catalog, with matching placeholders, and no stale entry |
| `tools/screenshot.py` | Regenerates `docs/screenshot.png` by off-screen GTK rendering (full page, 3 columns at 1400 px, `--lang`) |
| `README.md` / `docs/INSTALL.md` | GitHub page and step-by-step installation guide (GitHub anchors checked) |

**Publishing:** the repository targets `https://github.com/Radyum/Fantastic` (MIT license, copyright "The Fantastic contributors"). No git repository is initialized yet: the user publishes it.

**Common fan interface** (duck typing, no base class): `id`, `device_id`, `channel`, `index`, `label` (str or `Msg`), `controllable`, `min_percent`. Methods: `read() -> {rpm, percent, mode}`, `control_state()` (`pwmN_enable` value to remember), `apply(pct)`, `is_applied(pct)`, `restore(original)`. A new source (e.g. liquidctl) must provide the same interface and be added in `Hardware.scan()`.

**Stable identifiers:** `<chip_name>@usb-<port>`, `@pci-<address>` or `@<platform device>`, followed by `/pwmN`, `/fanN` or `/tempN`. NVIDIA: `nvidia@pci-0000:09:00.0/fan0`. The kernel's `hwmonN` numbers are never used, since they change on every boot. Identifiers are keys in `/var/lib/fantastic/state.json`.

**Protocol:** one JSON request per line, e.g. `{"cmd": "status"|"set"|"set_all"|"auto"|"auto_all"|"rename"|"hide"|"unhide_all"|"profile_save"|"profile_apply"|"profile_delete"|"rescan", "lang": "fr", "fan": ..., "percent": ..., "name": ..., "hidden": true|false}`. Response: `{"ok": true, ...}` or `{"ok": false, "error": "..."}`.
- `status` is public. Other commands require the client UID (`SO_PEERCRED`) to be root, in `allowed_users`, or in one of `allowed_groups`.
- `lang` selects the language of every text in the response (device names, labels, hints, errors). Default: English.
- `set_all` and `auto_all` return `errors` (id → message) instead of failing as a whole.
- **Hiding** is display-only; a fan's setting never changes. `set_all` (20% / 100% buttons) skips hidden fans. `auto_all` includes them, for safety. The CLI keeps the full numbering, hidden fans included, so `fantastic set N` stays consistent.

**Persistent state** (`state.json`): `targets` (percent targets), `originals` (original `pwmN_enable`, remembered before switching to manual), `names` (custom names), `hidden` (hidden fan ids), `profiles` (name → {fan id: percent, null = automatic}; names 1-10 characters, 8 profiles max; applying skips fans that disappeared; `status` lists the names in `profiles`).

## Translations

- Languages: English (source), German, Spanish, French, Italian: `LANGUAGES`, `CATALOGS` and `SINGULAR` (plural rule) in `fantastic/i18n.py`, one catalog per language in `fantastic/translations/<code>.py`.
- In the GUI and CLI, translate right away with `_("...", **params)` and `ngettext(singular, plural, n, **params)` (the current language is process-wide).
- In the hardware layer and the daemon, build `Msg("...", **params)` or `Joined([...])`: they are rendered later with `render(value, lang)` in the language of each client. `str(msg)` gives English (used in logs).
- Msgids use `{name}` placeholders; plural entries are `(singular, plural)` tuples and receive `{n}`. Keep each msgid a single literal (implicit concatenation is fine), because `tests/test_i18n.py` extracts them with `ast`.
- **Adding or changing a user-facing text means updating every catalog**: the tests fail otherwise.
- Units and separators come from `fmt.py` (`SEPARATORS`) and from the `"{value} RPM"` / `"{value}%"` msgids.
- GUI: language menu (flags) in the header bar, `win.language` stateful action, choice saved in `~/.config/fantastic/settings.json`, default from `i18n.system_language()` (`FANTASTIC_LANG`, `LANGUAGE`, `LC_ALL`, `LC_MESSAGES`, `LANG`). Switching rebuilds every row (`_signature` includes the data language).

**GUI layout:**
- Hints span the full width (`top_box`). Device blocks are spread over columns (`columns`).
- The number of columns comes from `Adw.Breakpoint`: 2 columns from 900 sp, 3 from 1380 sp (`BREAKPOINTS`). `notify::current-breakpoint` triggers `_layout()` on the next main loop iteration.
- `_layout()` puts each block into the shortest column. Heights are estimated with the `*_ROW_H` constants, not measured.
- Maximum width is bounded by an `Adw.Clamp` at 640 px per column.
- The window's `width_request` / `height_request` are mandatory with breakpoints.
- No `Adw.PreferencesPage`: it limits the width to a single column.

## Driver quirks (verified)

- **hwmon convention:** `pwmN` ranges from 0 to 255. `pwmN_enable` is 1 for manual; any other value is a driver-specific automatic mode (0 usually means "no control, full speed").
- **`nzxt_kraken3`** (chip names `x53`, `z53`, `kraken2023`…):
  - `pwm_enable` is 0 (forces 100%, and the value at driver load), 1 (manual) or 2 (curve).
  - Writing `pwmN` outside manual mode only stores the value; switching to 1 applies it.
  - The pump has a 20% minimum, enforced by the driver.
  - The `tempN_auto_point1..40_pwm` curves map to a 20-59 °C coolant and are 0 at load.
  - Fantastic's "auto" therefore programs `KRAKEN3_AUTO_CURVE` (30% up to 30 °C, like the factory setting) then sets `enable` to 2. Restoring 0 would put the pump at 100%.
- **`nct6775`**: `pwm_enable` is 0 (full speed), 1 (manual), 2 to 4 (cruise modes), 5 (SmartFan IV, the usual BIOS setting). In manual mode at 255, the driver **reports 0**: `HwmonFan.is_applied()` treats that as applied (otherwise the service rewrote it every 2 s). This driver **is not loaded by default** on Ubuntu.
- **`amdgpu`** refuses writing `pwm1` outside manual mode, which is why `HwmonFan.apply()` ignores the error of the first write.
- **NVML:**
  - Reading works without privileges. Setting (`nvmlDeviceSetFanSpeed_v2`) requires root.
  - Back to automatic goes through `nvmlDeviceSetDefaultFanSpeed_v2`.
  - The minimum comes from `nvmlDeviceGetMinMaxFanSpeed` (30% on the RTX 3080).
  - **Calibration** (`nvidia_start_percent`, default 43, measured by the user: the fans only spin from 43%): `to_raw`/`to_logical` in `nvidia.py` remap the slider so logical 5% = 43% NVML and 0-5% = 30-43% (stopped). Fans expose `stop_below` (5) in `status`; GUI and CLI warn below it. The round trip is only exact within 1 point.
  - `Hardware.scan()` retries `nvmlInit` on every scan, in case the driver is not ready at boot.
- **`asus_ec_sensors`** (chip `asusec`): chipset and VRM fans are **read-only**. The `T_Sensor` probe reports -40 °C when nothing is plugged in, and is hidden.

## Reference machine (the user's)

- Pop!_OS 24.04 (COSMIC, Wayland), kernel 7.2, Python 3.12. The user's system language is French.
- **ASUS ROG STRIX X570-I GAMING** motherboard, Ryzen 7 5700X3D (Tctl through `k10temp`).
- **NZXT Kraken X53** (USB 1e71:2007, `x53@usb-1-5`): only the pump is controllable (`pwm1`). The **2 radiator fans are on the motherboard's CPU_FAN**.
- **Case fan on CHA_FAN.**
- `nct6775` loaded through `/etc/modules-load.d/fantastic.conf` (chip `nct6798@nct6775.656`). Headers observed on 2026-10-29:
  - `pwm1` = **CHA_FAN** (Noctua case fan), renamed "Noctua boitier" by the user;
  - `pwm2` = **CPU_FAN** (the 2 NZXT radiator fans), renamed "NZXT CPU";
  - `pwm5`: follows the pump speed reported over USB: the Kraken's tachometer cable on AIO_PUMP; driving it has no effect;
  - `pwm7`: 0 RPM, nothing connected (the user had set it to manual 100%).
- Chipset and VRM fans: read-only through `asusec`.
- **RTX 3080** (`nvidia@pci-0000:09:00.0`), 2 fans, driver 595.
- A **pre-existing rule that does not belong to Fantastic**, `/etc/udev/rules.d/60-fan-control.rules`, makes every hwmon `pwm*` world-writable (`chmod a+w`). Fantastic does not need it. The user has been told.

## Ideas

- Custom speed/temperature curves (per fan, with a chosen temperature source) in the service.
- liquidctl source for USB devices without a kernel driver.
- Motherboard header identification assistant (vary one output and watch the RPM).
- .deb or Flatpak package for the GUI.

## Log

Add an entry for every session.

### 2026-10-29/30: v0.1.0, first session

**Built:** service, CLI, GTK4 interface; Auto / 20% / 100% buttons (`set_all` / `auto_all`); adaptive 1-3 column layout; flat-design icon; hideable fans (crossed-out eye with an "Undo" toast, 👁 *n* button with an `Adw.AlertDialog` confirmation, CLI `hide` / `unhide` / `list --all`); `install.sh` / `uninstall.sh`; GitHub README with screenshot, `docs/INSTALL.md` guide, MIT license; everything converted to English with a UI in five languages (flag menu); 36 tests.

**Verified on the reference machine:**
- Tests on Python 3.12 (host) and 3.13.
- Full detection: 9 fans, 7 controllable.
- `sudo ./install.sh`, run by the user: service active and enabled, `nct6775` made permanent.
- **Real test approved by the user:** `pwm1`, `pwm2`, the Kraken pump and RTX 3080 fan 0 went to 60% (RPM up), then back to Auto, with original modes restored (nct `enable` = 5, Kraken `enable` = 2, NVIDIA default policy).
- The user used the GUI (renamed and set `pwm1`/`pwm2` to about 25%).
- Rendering checked at 600, 1000 and 1400 px, in all five languages (de, en, fr, it captured; es checked through the CLI); hide/unhide flow and language switching driven in the real window with a test service.

**Pending on the user's side:** run `sudo ./install.sh` again to deploy the latest code (the installed service predates hiding, translations, the softer Kraken curve and the nct6775 full-speed fix), then `fantastic auto x53` to rewrite the Kraken curve (match by identifier: names depend on the language). Suggest setting `pwm7` back to Auto and hiding it, and hiding `pwm5`.
