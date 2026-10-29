"""Fans and temperatures exposed by the kernel in /sys/class/hwmon.

hwmon convention: pwmN (0-255) drives fan N, pwmN_enable selects the mode
(1 = manual, any other value = the driver's own automatic control) and
fanN_input reports the measured speed in RPM.
"""

from __future__ import annotations

import os
import re
import stat

from . import identify
from .i18n import Msg
from .identify import read_str

PWM_RE = re.compile(r"^pwm(\d+)$")
FAN_RE = re.compile(r"^fan(\d+)_input$")
TEMP_RE = re.compile(r"^temp(\d+)_input$")

MANUAL = 1

# nzxt-kraken3 driver: pwmN_enable is 0 (100%), 1 (manual) or 2 (curve).
# The driver starts at 0 without knowing the factory setting, so "automatic"
# means programming a sensible curve based on the coolant temperature.
KRAKEN3_CHIPS = {"x53", "z53", "kraken2023", "kraken2023elite", "kraken2024elite"}
KRAKEN3_PUMP_MIN = 20  # the driver refuses less than 20% on the pump
KRAKEN3_CURVE_POINTS = 40  # points 1 to 40 = 20 to 59 °C
KRAKEN3_AUTO_CURVE = [(20, 30), (30, 30), (35, 45), (40, 65), (45, 85), (50, 100)]

# Labels provided by drivers, replaced by clearer, translatable ones.
DRIVER_LABELS = {
    "Pump speed": Msg("Pump"),
    "Fan speed": Msg("Fans"),
    "Coolant temp": Msg("Coolant"),
    "VRM HS": Msg("VRM heatsink"),
    "CPU Fan": Msg("CPU fan"),
    "CPU_Opt": "CPU_OPT",
    "Water_Pump": Msg("Pump (W_PUMP)"),
}


def label_for(chip: HwmonChip, kind: str, index: int) -> str | Msg | None:
    label = read_str(chip.attr(f"{kind}{index}_label"))
    return DRIVER_LABELS.get(label, label) if label else None


def read_int(path: str) -> int | None:
    value = read_str(path)
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def write_value(path: str, value: int) -> None:
    with open(path, "w") as f:
        f.write(str(value))


def percent_to_raw(percent: int) -> int:
    return round(percent * 255 / 100)


def raw_to_percent(raw: int) -> int:
    return round(raw * 100 / 255)


def interpolate(curve: list[tuple[int, int]], x: int) -> int:
    if x <= curve[0][0]:
        return curve[0][1]
    for (x0, y0), (x1, y1) in zip(curve, curve[1:]):
        if x <= x1:
            return round(y0 + (y1 - y0) * (x - x0) / (x1 - x0))
    return curve[-1][1]


class HwmonChip:
    """A hwmon chip (/sys/class/hwmon/hwmonN) and the device that carries it."""

    def __init__(self, path: str, sysfs_root: str, dmi: dict[str, str]):
        self.path = path
        self.name = read_str(os.path.join(path, "name")) or os.path.basename(path)
        device = os.path.join(path, "device")
        self.dev_path = os.path.realpath(device) if os.path.exists(device) else None
        if self.dev_path:
            self.bus = identify.bus_info(self.dev_path, sysfs_root)
        else:
            self.bus = {"bus": "virtual", "address": os.path.basename(path)}
        driver_link = os.path.join(device, "driver")
        if os.path.exists(driver_link):
            self.driver = os.path.basename(os.path.realpath(driver_link))
        else:
            self.driver = self.name
        title, self.kind = identify.identify_chip(self.name)
        self.display_name, self.details = identify.describe_device(
            title, self.kind, self.bus, self.driver, self.dev_path, dmi)
        self.id = self._stable_id()

        try:
            attrs = os.listdir(path)
        except OSError:
            attrs = []
        self.pwm_indices = sorted(int(m[1]) for a in attrs if (m := PWM_RE.match(a)))
        self.fan_indices = sorted(int(m[1]) for a in attrs if (m := FAN_RE.match(a)))
        self.temp_indices = sorted(int(m[1]) for a in attrs if (m := TEMP_RE.match(a)))

    def _stable_id(self) -> str:
        # hwmonN numbers change from one boot to the next: rely on the physical
        # location instead (USB port, PCI address, platform device name).
        bus = self.bus["bus"]
        if bus in ("usb", "pci"):
            return f"{self.name}@{bus}-{self.bus['address']}"
        return f"{self.name}@{self.bus['address']}"

    def attr(self, name: str) -> str:
        return os.path.join(self.path, name)

    def device_info(self) -> dict:
        return {"id": self.id, "name": self.display_name, "kind": self.kind,
                "driver": self.driver, "details": self.details}

    def fans(self) -> list[HwmonFan]:
        fans = []
        for index in sorted(set(self.pwm_indices) | set(self.fan_indices)):
            has_pwm = index in self.pwm_indices
            fans.append(HwmonFan(self, index, has_pwm, has_pwm and self._writable(f"pwm{index}")))
        return fans

    def temps(self) -> list[HwmonTemp]:
        temps = []
        for index in self.temp_indices:
            temp = HwmonTemp(self, index)
            value = temp.read()
            # Unconnected probes report 0 °C or -40 °C (e.g. Nuvoton PCH_*, ASUS T_Sensor).
            if value is not None and 0 < value < 150:
                temps.append(temp)
        return temps

    def _writable(self, attr: str) -> bool:
        try:
            return bool(os.stat(self.attr(attr)).st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
        except OSError:
            return False


class HwmonFan:
    def __init__(self, chip: HwmonChip, index: int, has_pwm: bool, controllable: bool):
        self.chip = chip
        self.index = index
        self.has_pwm = has_pwm
        self.controllable = controllable
        self.channel = f"pwm{index}" if has_pwm else f"fan{index}"
        self.id = f"{chip.id}/{self.channel}"
        self.device_id = chip.id
        self.label = label_for(chip, "fan", index) or label_for(chip, "pwm", index) or Msg("Fan {n}", n=index)
        self.kraken3 = chip.name in KRAKEN3_CHIPS
        self.min_percent = KRAKEN3_PUMP_MIN if self.kraken3 and index == 1 else 0
        self._pwm = chip.attr(f"pwm{index}")
        self._enable = chip.attr(f"pwm{index}_enable")

    def read(self) -> dict:
        rpm = read_int(self.chip.attr(f"fan{self.index}_input"))
        if not self.has_pwm:
            return {"rpm": rpm, "percent": None, "mode": None}
        raw = read_int(self._pwm)
        enable = read_int(self._enable)
        if enable is None:
            mode = "unknown"
        else:
            mode = "manual" if enable == MANUAL else "auto"
        return {"rpm": rpm, "percent": None if raw is None else raw_to_percent(raw), "mode": mode}

    def control_state(self) -> int | None:
        """Current mode (pwmN_enable), to remember before taking control."""
        return read_int(self._enable)

    def apply(self, percent: int) -> None:
        raw = percent_to_raw(percent)
        # Writing the value before switching to manual avoids a jolt on drivers that
        # apply the stored value when the mode changes (nct6775, nzxt-kraken3).
        # Others (amdgpu) refuse this write outside manual mode: ignore the error.
        try:
            write_value(self._pwm, raw)
        except OSError:
            pass
        if os.path.exists(self._enable) and read_int(self._enable) != MANUAL:
            write_value(self._enable, MANUAL)
        write_value(self._pwm, raw)

    def is_applied(self, percent: int) -> bool:
        target = percent_to_raw(percent)
        if os.path.exists(self._enable):
            enable = read_int(self._enable)
            # nct6775 reports manual mode at 255 as 0 ("no control, full speed"): same result.
            if enable != MANUAL and not (enable == 0 and target == 255):
                return False
        raw = read_int(self._pwm)
        return raw is not None and abs(raw - target) <= 3

    def restore(self, original: int | None) -> None:
        """Hands control back to the hardware's automatic mode."""
        if not os.path.exists(self._enable):
            return  # this driver exposes no automatic mode
        if self.kraken3:
            for point in range(1, KRAKEN3_CURVE_POINTS + 1):
                duty = interpolate(KRAKEN3_AUTO_CURVE, 19 + point)
                write_value(self.chip.attr(f"temp{self.index}_auto_point{point}_pwm"), percent_to_raw(duty))
            write_value(self._enable, 2)
            return
        nuvoton = self.chip.name.startswith("nct6")
        # On Nuvoton chips, 0 ("no control, full speed") is what the driver reports for a fan
        # held at 255, so it is never a real original mode: use SmartFan IV (5) instead.
        if original is None or original == MANUAL or (nuvoton and original == 0):
            original = 5 if nuvoton else 2
        write_value(self._enable, original)


class HwmonTemp:
    def __init__(self, chip: HwmonChip, index: int):
        self.chip = chip
        self.index = index
        self.id = f"{chip.id}/temp{index}"
        self.device_id = chip.id
        self.kind = chip.kind
        self.label = label_for(chip, "temp", index) or Msg("Temperature {n}", n=index)
        self._input = chip.attr(f"temp{index}_input")

    def read(self) -> float | None:
        value = read_int(self._input)
        return None if value is None else value / 1000


def scan(sysfs_root: str = "/sys") -> list[HwmonChip]:
    base = os.path.join(sysfs_root, "class", "hwmon")
    try:
        entries = os.listdir(base)
    except OSError:
        return []
    dmi = identify.read_dmi(sysfs_root)
    entries.sort(key=lambda e: int(e[5:]) if e[5:].isdigit() else 0)
    return [HwmonChip(os.path.join(base, e), sysfs_root, dmi) for e in entries if e.startswith("hwmon")]
