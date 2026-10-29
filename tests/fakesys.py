"""Builds a fake sysfs tree for the tests."""

from __future__ import annotations

import os


class FakeSys:
    def __init__(self, root: str):
        self.root = root
        self._count = 0
        os.makedirs(os.path.join(root, "class", "hwmon"))

    def write(self, relpath: str, content) -> str:
        path = os.path.join(self.root, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(f"{content}\n")
        return path

    def read(self, relpath: str) -> str:
        with open(os.path.join(self.root, relpath)) as f:
            return f.read().strip()

    def add_chip(self, name: str, devpath: str, attrs: dict) -> str:
        """Adds /class/hwmon/hwmonN -> /devices/<devpath>/hwmon/hwmonN; returns the relative path."""
        hwmon = f"hwmon{self._count}"
        self._count += 1
        dev_dir = os.path.join(self.root, "devices", devpath)
        chip_dir = os.path.join(dev_dir, "hwmon", hwmon)
        os.makedirs(chip_dir)
        os.symlink(os.path.relpath(dev_dir, chip_dir), os.path.join(chip_dir, "device"))
        os.symlink(os.path.relpath(chip_dir, os.path.join(self.root, "class", "hwmon")),
                   os.path.join(self.root, "class", "hwmon", hwmon))
        rel = os.path.relpath(chip_dir, self.root)
        self.write(os.path.join(rel, "name"), name)
        for attr, value in attrs.items():
            self.write(os.path.join(rel, attr), value)
        return rel


def build_desktop(root: str) -> tuple[FakeSys, dict[str, str]]:
    """Typical machine: Nuvoton motherboard, USB Kraken X53, AMD CPU and read-only ASUS EC."""
    fs = FakeSys(root)
    fs.write("class/dmi/id/board_vendor", "ASUSTeK COMPUTER INC.")
    fs.write("class/dmi/id/board_name", "ROG STRIX X570-I GAMING")
    fs.write("class/dmi/id/chassis_type", "3")
    chips = {
        "nct": fs.add_chip("nct6798", "platform/nct6775.656", {
            "pwm1": 128, "pwm1_enable": 5, "fan1_input": 900,
            "pwm2": 200, "pwm2_enable": 5, "fan2_input": 1500,
            "temp1_input": 35000, "temp1_label": "SYSTIN",
        }),
        "kraken": fs.add_chip("x53", "pci0000:00/0000:00:01.2/usb1/1-5/1-5:1.0/0003:1E71:2007.0009", {
            "pwm1": 77, "pwm1_enable": 0, "fan1_input": 1045, "fan1_label": "Pump speed",
            "temp1_input": 29600, "temp1_label": "Coolant temp",
            **{f"temp1_auto_point{i}_pwm": 0 for i in range(1, 41)},
        }),
        "k10": fs.add_chip("k10temp", "pci0000:00/0000:00:18.3", {
            "temp1_input": 45000, "temp1_label": "Tctl",
        }),
        "ec": fs.add_chip("asusec", "platform/asus-ec-sensors", {
            "fan1_input": 3200, "fan1_label": "Chipset",
            "temp1_input": -40000, "temp1_label": "T_Sensor",
        }),
    }
    fs.write("devices/pci0000:00/0000:00:01.2/usb1/1-5/idVendor", "1e71")
    fs.write("devices/pci0000:00/0000:00:01.2/usb1/1-5/idProduct", "2007")
    fs.write("devices/pci0000:00/0000:00:01.2/usb1/1-5/product", "NZXT USB Device")
    fs.write("devices/pci0000:00/0000:00:18.3/vendor", "0x1022")
    fs.write("devices/pci0000:00/0000:00:18.3/device", "0x1443")
    return fs, chips
