# Fantastic installation guide

This guide takes you from nothing to identified, controlled fans. Allow about ten minutes. It requires no particular Linux knowledge, only opening a terminal and copying commands.

**Contents**

1. [Check compatibility](#1-check-compatibility)
2. [Download Fantastic](#2-download-fantastic)
3. [Run the installer](#3-run-the-installer)
4. [First launch](#4-first-launch)
5. [Identify your fans](#5-identify-your-fans)
6. [Fans missing?](#6-fans-missing)
7. [Other distributions (Fedora, Arch…)](#7-other-distributions-fedora-arch)
8. [Update](#8-update)
9. [Uninstall](#9-uninstall)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Check compatibility

Fantastic works on distributions that provide **GTK 4** and **libadwaita 1.5 or newer**, with **systemd**:

| Distribution | Compatible | Method |
|---|---|---|
| Ubuntu 24.04 LTS and newer | ✅ | `install.sh` installs everything |
| Pop!_OS 24.04, Linux Mint 22 and other Ubuntu 24.04 derivatives | ✅ | `install.sh` installs everything |
| Debian 13 (Trixie) | ✅ | `install.sh` installs everything |
| Fedora 40 and newer, Arch Linux, openSUSE Tumbleweed | ✅ | Dependencies to install by hand, see [§ 7](#7-other-distributions-fedora-arch) |
| Ubuntu 22.04, Debian 12 | ❌ | libadwaita too old |

Not sure which version you have? Run:

```bash
cat /etc/os-release
```

## 2. Download Fantastic

Open a terminal (<kbd>Ctrl</kbd>+<kbd>Alt</kbd>+<kbd>T</kbd> on Ubuntu), then choose **one** of the two methods.

**With git** (recommended, since updates are then easier):

```bash
sudo apt install git
git clone https://github.com/Radyum/Fantastic.git
cd Fantastic
```

**Without git:**

1. Open [github.com/Radyum/Fantastic](https://github.com/Radyum/Fantastic).
2. Click the green **Code** button, then **Download ZIP**.
3. Extract the archive: right click → *Extract here*.
4. In the terminal, go to the extracted folder, for example:

```bash
cd ~/Downloads/Fantastic-main
```

## 3. Run the installer

From the Fantastic folder:

```bash
sudo ./install.sh
```

You will be asked for your password: this is expected, since the installer creates a system service. Here is what the script does, step by step:

| Step | What happens |
|---|---|
| **Dependencies** | Installs `python3-gi`, `gir1.2-gtk-4.0` and `gir1.2-adw-1` with apt |
| **Copying the program** | Files copied to `/opt/fantastic`, `fantastic` command created in `/usr/local/bin` |
| **Configuration** | Creates `/etc/fantastic/config.json`, which allows you to set fan speeds |
| **Desktop launcher** | **Fantastic** appears in the applications menu |
| **Motherboard driver** | If motherboard fans are invisible, the script offers to load their driver (see below) |
| **Service** | Starts `fantasticd`, then lists the detected fans |

### The motherboard driver question

On most desktop PCs, the script asks:

```
Motherboard fans are not visible. Load the nct6775 driver (now and at every boot)? [Y/n]
```

Answer **Y** (or just press <kbd>Enter</kbd>). This driver gives access to the CPU_FAN, CHA_FAN… headers of the motherboard. It does not change any speed by itself.

### Expected result

The installation ends with the list of fans found, for example:

```
#  Name            Device                             Speed  Duty  Mode   Identifier
─  ──────────────  ─────────────────────────────  ─────────  ────  ─────  ────────────────────────────
1  Pump            NZXT Kraken X53 / X63 / X73    1,054 RPM   30%  auto   x53@usb-1-5/pwm1
2  Fan 1           NVIDIA GeForce RTX 3080          751 RPM   45%  auto   nvidia@pci-0000:09:00.0/fan0
3  Fan 2           NVIDIA GeForce RTX 3080          745 RPM   45%  auto   nvidia@pci-0000:09:00.0/fan1
4  Fan 1           Motherboard (Nuvoton NCT6798)    827 RPM   38%  auto   nct6798@nct6775.656/pwm1
5  Fan 2           Motherboard (Nuvoton NCT6798)  1,695 RPM   38%  auto   nct6798@nct6775.656/pwm2
…
```

Nothing shows up, or an error appears? See [Troubleshooting](#10-troubleshooting).

## 4. First launch

Open **Fantastic** from the applications menu. You can also type `fantastic gui` in a terminal.

![Fantastic window](screenshot.png)

The window is organized by **device**: liquid cooler, graphics card, motherboard… Depending on the window width, the blocks spread over one, two or three columns. Each fan has its own row:

- **its name and measured speed**, in revolutions per minute;
- **the Auto switch**: when on, the hardware (BIOS, graphics card, firmware) decides the speed;
- **the slider**: move it and the fan switches to manual at the chosen duty;
- **the pencil**, to rename the fan;
- **the crossed-out eye**, to hide it if it is useless to you (an empty header, for example).

At the top, the **Auto**, **20%**, **50%** and **100%** buttons act on every visible fan at once. That's handy for a quiet PC in one click, or to check that everything spins. The **Auto** button also puts hidden fans back into automatic mode.

Next to them, the **+** button saves the current settings of all fans as a **profile** with a name of up to 10 characters (for example "Quiet" or "Gaming"). Each profile then gets its own button, to apply it in one click.

When fans are hidden, a **👁** button appears at the top left, with their number. It shows them all again, after confirmation. Hiding a fan never changes its setting.

The **flag** at the top right switches the language: 🇬🇧 English, 🇩🇪 Deutsch, 🇪🇸 Español, 🇫🇷 Français or 🇮🇹 Italiano. By default, Fantastic follows the system language.

Your settings are kept when you close the window, and after a reboot.

## 5. Identify your fans

Graphics cards and liquid coolers are named automatically. Motherboard headers, however, show up as "Fan 1", "Fan 2"… because Linux does not know the name printed on the board (CPU_FAN, CHA_FAN…).

To identify them:

1. **Spot empty headers.** A header at **0 RPM** has nothing connected: hide it with the crossed-out eye.
2. **Run a header at full speed.** Drag its slider to **100%**, with the case open or by ear. The fan that speeds up is the one on this header.
3. **Rename it.** Click the pencil, then type for example "Radiator (CPU_FAN)" or "Rear case fan (CHA_FAN)".
4. **Hand it back to the hardware.** Turn **Auto** back on, or choose the speed that suits you.
5. Repeat for each header.

> 💡 **A header whose speed does not change when the slider moves** often only carries a measurement. Typically, it is the tachometer cable of a liquid cooler pump plugged into AIO_PUMP while the pump is powered elsewhere. Control the pump from its own row (for example "NZXT Kraken"), and hide this header or rename it "Pump (tach)".

## 6. Fans missing?

Start with the **suggestions** shown at the top of the window, or at the bottom of `fantastic list`. Fantastic detects most of the cases below and suggests the command to run.

### Motherboard fans

Load the driver of the controller chip:

```bash
sudo modprobe nct6775        # ASUS, MSI, ASRock (Nuvoton chips)
sudo modprobe it87           # Gigabyte (ITE chips)
```

Then click ⟳ in Fantastic. If the fans show up, make the loading permanent:

```bash
echo nct6775 | sudo tee /etc/modules-load.d/fantastic.conf
```

Still nothing? See "`modprobe nct6775` shows nothing" in [Troubleshooting](#10-troubleshooting).

### NVIDIA graphics card

The **proprietary NVIDIA driver** is required. The open-source `nouveau` driver cannot set fan speeds. To check:

```bash
nvidia-smi
```

If the command shows your card, Fantastic will find it. Otherwise, install the driver from Ubuntu's *Additional Drivers* tool, or with `sudo ubuntu-drivers install`.

### AMD graphics card

Nothing to do: the `amdgpu` driver is always loaded.

### Laptops

- **ThinkPad:** fan control is disabled by default. Enable it, then reboot:

  ```bash
  echo 'options thinkpad_acpi fan_control=1' | sudo tee /etc/modprobe.d/thinkpad_acpi.conf
  ```

- **Other brands:** many laptops do not let Linux drive their fan. Fantastic then shows the speed at best, read-only.

### Liquid coolers and USB controllers

The models listed in the [README](../README.md#supported-hardware) are recognized automatically with a recent kernel. Others (some Corsair iCUE devices, NZXT Smart Device V1…) are not supported yet.

## 7. Other distributions (Fedora, Arch…)

Install the dependencies with your distribution's package manager, then run the installer with `--no-apt`:

```bash
# Fedora
sudo dnf install python3-gobject gtk4 libadwaita

# Arch Linux / Manjaro
sudo pacman -S python-gobject gtk4 libadwaita

# openSUSE Tumbleweed
sudo zypper install python3-gobject typelib-1_0-Gtk-4_0 typelib-1_0-Adw-1

# Then, in every case:
sudo ./install.sh --no-apt
```

On these distributions, administrators belong to the `wheel` group, which is already allowed by default.

## 8. Update

```bash
cd Fantastic
git pull
sudo ./install.sh
```

Your configuration, settings and fan names are kept. If you downloaded a ZIP, download a new one and run `sudo ./install.sh` again from the new folder.

## 9. Uninstall

```bash
sudo ./uninstall.sh            # keeps the configuration and settings
sudo ./uninstall.sh --purge    # removes everything
```

Fans go back to automatic mode as soon as the service stops. If the installation added `/etc/modules-load.d/fantastic.conf`, it is kept (the motherboard driver keeps loading at boot). Remove it by hand if you no longer want it.

## 10. Troubleshooting

<details>
<summary><b>"fantasticd service unreachable"</b></summary>

The service is not running. Check its status and read its log:

```bash
systemctl status fantasticd
journalctl -u fantasticd -n 50
```

To restart it: `sudo systemctl restart fantasticd`.
</details>

<details>
<summary><b>Sliders are greyed out / "not authorized"</b></summary>

Your account is not allowed to change speeds. Add your user name to `allowed_users` in `/etc/fantastic/config.json`:

```json
"allowed_users": ["your-name"],
```

Then reload the configuration: `sudo systemctl reload fantasticd`.
</details>

<details>
<summary><b><code>modprobe nct6775</code> shows nothing</b></summary>

Look at the kernel messages:

```bash
sudo dmesg | grep -iE 'nct6775|it87|resource conflict'
```

- **"ACPI resource conflict"**: the BIOS reserves the chip. On recent ASUS boards, the driver goes through a WMI interface that works around the problem if the kernel knows the board. A newer kernel may therefore be enough. As a last resort, there is the `acpi_enforce_resources=lax` boot parameter, to be used knowingly.
- **Gigabyte:** the kernel's `it87` driver does not support every recent chip. The out-of-tree [frankcrawford/it87](https://github.com/frankcrawford/it87) driver covers more models.
</details>

<details>
<summary><b>A slider jumps back to another value on its own</b></summary>

Another fan control program is probably running at the same time: CoolerControl, fancontrol, liquidctl in a scheduled task, vendor software… Keep only one.
</details>

<details>
<summary><b>My NVIDIA card's fan does not go below 30%</b></summary>

That is the minimum imposed by the card in manual mode. In **Auto** mode, however, the card can stop its fans when idle (0 dB mode).
</details>

<details>
<summary><b>A "Thermal failsafe" banner shows up</b></summary>

The processor or graphics card exceeded 90 °C. Manually set fans were put at 100%, and they return to their target when the temperature drops by 10 °C. If your processor normally runs close to this threshold (some Ryzen 7000 target 95 °C under load), raise `failsafe_temp` in `/etc/fantastic/config.json`.
</details>

<details>
<summary><b>The interface is in the wrong language</b></summary>

Pick the language from the flag menu at the top right: the choice is remembered. The command line follows the system language; `FANTASTIC_LANG=en fantastic list` forces it (`en`, `de`, `es`, `fr` or `it`).
</details>

<details>
<summary><b>Nothing matches, I need help</b></summary>

Open an [issue](https://github.com/Radyum/Fantastic/issues) and attach:

```bash
fantastic detect
cat /sys/class/dmi/id/board_vendor /sys/class/dmi/id/board_name
uname -r
```
</details>
