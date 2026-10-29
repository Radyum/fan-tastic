"""Human-readable identification of hwmon chips and of the devices that carry them."""

from __future__ import annotations

import functools
import os
import re

from .i18n import Joined, Msg

# Display order of device kinds.
KIND_ORDER = ["aio", "gpu", "motherboard", "controller", "laptop", "psu", "cpu", "storage", "other"]

# hwmon chip name -> (title, kind)
KNOWN_CHIPS = {
    # Motherboard sensors other than Super I/O chips
    "asusec": (Msg("Motherboard ({chip})", chip="ASUS EC"), "motherboard"),
    "asus_wmi_sensors": (Msg("Motherboard ({chip})", chip="ASUS WMI"), "motherboard"),
    "gigabyte_wmi": (Msg("Motherboard ({chip})", chip="Gigabyte WMI"), "motherboard"),
    "asus": ("ASUS WMI", "laptop"),
    # Processors
    "k10temp": (Msg("AMD processor"), "cpu"),
    "zenpower": (Msg("AMD processor"), "cpu"),
    "coretemp": (Msg("Intel processor"), "cpu"),
    # Graphics cards
    "amdgpu": (Msg("AMD graphics card"), "gpu"),
    "radeon": (Msg("AMD graphics card"), "gpu"),
    "nouveau": (Msg("NVIDIA graphics card"), "gpu"),
    "i915": (Msg("Intel graphics card"), "gpu"),
    "xe": (Msg("Intel graphics card"), "gpu"),
    # All-in-one liquid coolers and USB controllers
    "x53": ("NZXT Kraken X53 / X63 / X73", "aio"),
    "z53": ("NZXT Kraken Z53 / Z63 / Z73", "aio"),
    "kraken2023": ("NZXT Kraken (2023)", "aio"),
    "kraken2023elite": ("NZXT Kraken Elite (2023)", "aio"),
    "kraken2024elite": ("NZXT Kraken Elite (2024)", "aio"),
    "kraken2": ("NZXT Kraken X42 / X52 / X62 / X72", "aio"),
    "gigabyte_waterforce": ("Gigabyte AORUS Waterforce", "aio"),
    "rog_ryujin": ("ASUS ROG Ryujin II", "aio"),
    "d5next": ("Aquacomputer D5 Next", "aio"),
    "nzxtsmart2": ("NZXT Smart Device V2 / RGB & Fan Controller", "controller"),
    "corsaircpro": ("Corsair Commander Pro", "controller"),
    "octo": ("Aquacomputer Octo", "controller"),
    "quadro": ("Aquacomputer Quadro", "controller"),
    "aquaero": ("Aquacomputer Aquaero", "controller"),
    "pwmfan": (Msg("PWM fan"), "controller"),
    # Laptops and integrated machines
    "thinkpad": ("Lenovo ThinkPad", "laptop"),
    "dell_smm": ("Dell", "laptop"),
    "applesmc": ("Apple SMC", "laptop"),
    "steamdeck_hwmon": ("Steam Deck", "laptop"),
    "surface_fan": ("Microsoft Surface", "laptop"),
    # Miscellaneous
    "corsairpsu": (Msg("Corsair power supply"), "psu"),
    "nvme": (Msg("NVMe SSD"), "storage"),
    "drivetemp": (Msg("Disk"), "storage"),
    "acpitz": (Msg("ACPI thermal zone"), "other"),
}

# Name prefixes of Super I/O chips (motherboard fan controllers): (prefix, vendor, kind)
CHIP_PREFIXES = [
    ("nct6", "Nuvoton", "motherboard"),
    ("it8", "ITE", "motherboard"),
    ("f71", "Fintek", "motherboard"),
    ("w83", "Winbond", "motherboard"),
]

LAPTOP_CHASSIS = {"8", "9", "10", "11", "14", "30", "31", "32"}

PCI_ADDRESS = re.compile(r"^[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]$")
PCI_IDS_PATHS = ["/usr/share/misc/pci.ids", "/usr/share/hwdata/pci.ids", "/usr/share/pci.ids"]


def read_str(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except OSError:
        return None


def identify_chip(name: str) -> tuple[str | Msg, str]:
    """Returns (title, kind) for a hwmon chip name."""
    if name in KNOWN_CHIPS:
        return KNOWN_CHIPS[name]
    for prefix, vendor, kind in CHIP_PREFIXES:
        if name.startswith(prefix):
            return Msg("Motherboard ({chip})", chip=f"{vendor} {name.upper()}"), kind
    if name.startswith("iwlwifi"):
        return Msg("Intel Wi-Fi"), "other"
    return name, "other"


def read_dmi(sysfs_root: str) -> dict[str, str]:
    base = os.path.join(sysfs_root, "class", "dmi", "id")
    keys = ("board_vendor", "board_name", "sys_vendor", "product_name", "chassis_type")
    return {key: value for key in keys if (value := read_str(os.path.join(base, key)))}


def board_name(dmi: dict[str, str]) -> str | None:
    parts = [dmi.get("board_vendor"), dmi.get("board_name")]
    text = " ".join(p for p in parts if p)
    return text or None


def is_laptop(dmi: dict[str, str]) -> bool:
    return dmi.get("chassis_type") in LAPTOP_CHASSIS


@functools.lru_cache(maxsize=None)
def cpu_model() -> str | None:
    try:
        with open("/proc/cpuinfo", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return None


@functools.lru_cache(maxsize=None)
def pci_names(vendor_id: str, device_id: str) -> tuple[str | None, str | None]:
    """Looks up vendor and device names in the pci.ids database."""
    for path in PCI_IDS_PATHS:
        try:
            f = open(path, encoding="utf-8", errors="replace")
        except OSError:
            continue
        vendor = None
        with f:
            for line in f:
                if not line.strip() or line.startswith("#"):
                    continue
                if not line.startswith("\t"):
                    if vendor is not None:
                        break  # end of the vendor block: unknown device
                    if line[:4].lower() == vendor_id:
                        vendor = line[4:].strip()
                elif vendor is not None and not line.startswith("\t\t") and line[1:5].lower() == device_id:
                    return vendor, line[5:].strip()
        return vendor, None
    return None, None


def bus_info(dev_path: str, sysfs_root: str) -> dict[str, str]:
    """Walks up the sysfs tree to the USB or PCI device that carries the chip."""
    devices_root = os.path.join(sysfs_root, "devices")
    path = dev_path
    while path.startswith(devices_root + os.sep):
        base = os.path.basename(path)
        if os.path.isfile(os.path.join(path, "idVendor")):
            info = {"bus": "usb", "address": base}
            for key, attr in (("vendor_id", "idVendor"), ("product_id", "idProduct"),
                              ("manufacturer", "manufacturer"), ("product", "product")):
                if value := read_str(os.path.join(path, attr)):
                    info[key] = value
            return info
        if PCI_ADDRESS.match(base) and os.path.isfile(os.path.join(path, "vendor")):
            vendor_id = (read_str(os.path.join(path, "vendor")) or "").removeprefix("0x")
            device_id = (read_str(os.path.join(path, "device")) or "").removeprefix("0x")
            info = {"bus": "pci", "address": base, "vendor_id": vendor_id, "device_id": device_id}
            vendor_name, device_name = pci_names(vendor_id, device_id)
            if vendor_name:
                info["vendor"] = vendor_name
            if device_name:
                info["device"] = device_name
            return info
        path = os.path.dirname(path)
    bus = "platform" if f"{os.sep}platform{os.sep}" in dev_path else "virtual"
    return {"bus": bus, "address": os.path.basename(dev_path)}


def short_pci_name(device_name: str) -> str:
    """'GA102 [GeForce RTX 3080]' -> 'GeForce RTX 3080'."""
    match = re.search(r"\[([^\]]+)\]\s*$", device_name)
    return match.group(1) if match else device_name


def describe_device(title: str | Msg, kind: str, bus: dict[str, str], driver: str,
                    dev_path: str | None, dmi: dict[str, str]) -> tuple[str | Joined, Joined]:
    """Builds the displayed (name, details) of a device."""
    name = title
    if kind == "cpu" and (model := cpu_model()):
        name = model
    elif kind == "gpu" and bus.get("device"):
        name = Joined([title, short_pci_name(bus["device"])], sep=" ")
    elif dev_path and (model := read_str(os.path.join(dev_path, "model"))):
        name = Joined([title, model], sep=" ")

    details = []
    if bus["bus"] == "usb":
        ids = f"{bus.get('vendor_id', '?')}:{bus.get('product_id', '?')}"
        product = " ".join(p for p in (bus.get("manufacturer"), bus.get("product")) if p)
        details.append(f"USB {ids}" + (f" ({product})" if product else ""))
    elif bus["bus"] == "pci":
        details.append(f"PCI {bus['address']}")
    if kind == "motherboard" and (board := board_name(dmi)):
        details.append(board)
    details.append(Msg("driver {name}", name=driver))
    return name, Joined(details)
