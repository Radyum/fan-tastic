"""Hardware inventory: gathers fans and temperatures from every source."""

from __future__ import annotations

import logging
import os

from . import hwmon, identify, nvidia
from .i18n import DEFAULT_LANGUAGE, Msg, render
from .identify import read_str
from .nvidia import NvmlError

log = logging.getLogger(__name__)

READ_ERRORS = (OSError, NvmlError)


class Hardware:
    def __init__(self, sysfs_root: str = "/sys", use_nvidia: bool = True):
        self.sysfs_root = sysfs_root
        self.devices: dict[str, dict] = {}
        self.fans: dict = {}
        self.temps: dict = {}
        self.hints: list[dict] = []
        self._use_nvidia = use_nvidia
        self._nvml = None
        self._nvml_error = None
        self.scan()

    def close(self) -> None:
        if self._nvml is not None:
            try:
                self._nvml.shutdown()
            except NvmlError:
                pass
            self._nvml = None

    def scan(self) -> None:
        """(Re)builds the inventory. Identifiers stay stable from one scan to the next."""
        sources = []
        chips = hwmon.scan(self.sysfs_root)
        sources.extend(chips)
        if self._use_nvidia and self._nvml is None:
            # Retried on every scan: at boot, the NVIDIA driver may not be ready yet.
            try:
                self._nvml = nvidia.Nvml()
                self._nvml_error = None
            except NvmlError as exc:
                self._nvml_error = str(exc)
        if self._nvml is not None:
            try:
                sources.extend(nvidia.scan(self._nvml))
            except NvmlError as exc:
                log.warning("NVML: %s", exc)

        devices, fans, temps = {}, {}, {}
        for source in sources:
            try:
                source_fans, source_temps = source.fans(), source.temps()
            except READ_ERRORS as exc:
                log.warning("cannot read %s: %s", source.id, exc)
                continue
            if not source_fans and not source_temps:
                continue
            info = source.device_info()
            if info["id"] in devices:
                log.warning("duplicate identifier ignored: %s", info["id"])
                continue
            devices[info["id"]] = info
            fans.update((fan.id, fan) for fan in source_fans)
            temps.update((temp.id, temp) for temp in source_temps)

        order = {kind: i for i, kind in enumerate(identify.KIND_ORDER)}
        piloted = {fan.device_id for fan in fans.values() if fan.controllable}
        sorted_devices = sorted(devices.values(), key=lambda d: (
            order.get(d["kind"], 99), d["id"] not in piloted, str(d["name"]), d["id"]))
        self.devices = {d["id"]: d for d in sorted_devices}
        rank = {device_id: i for i, device_id in enumerate(self.devices)}

        def sort_key(item):
            return rank[item.device_id], item.index, item.id

        self.fans = {fan.id: fan for fan in sorted(fans.values(), key=sort_key)}
        self.temps = {temp.id: temp for temp in sorted(temps.values(), key=sort_key)}
        self.hints = self._compute_hints(chips)

    def snapshot(self, lang: str = DEFAULT_LANGUAGE) -> dict:
        """Current values as JSON-serializable data, with texts rendered in `lang`."""
        devices = [{**d, "name": render(d["name"], lang), "details": render(d["details"], lang)}
                   for d in self.devices.values()]
        fans = []
        for fan in self.fans.values():
            entry = {"id": fan.id, "device_id": fan.device_id, "channel": fan.channel,
                     "label": render(fan.label, lang), "controllable": fan.controllable,
                     "min_percent": fan.min_percent}
            try:
                entry.update(fan.read())
            except READ_ERRORS as exc:
                entry.update(rpm=None, percent=None, mode=None, error=str(exc))
            fans.append(entry)
        temps = []
        for temp in self.temps.values():
            try:
                celsius = temp.read()
            except READ_ERRORS:
                celsius = None
            temps.append({"id": temp.id, "device_id": temp.device_id, "label": render(temp.label, lang),
                          "kind": temp.kind, "celsius": celsius})
        return {"devices": devices, "fans": fans, "temps": temps}

    def render_hints(self, lang: str) -> list[dict]:
        return [{"text": render(hint["text"], lang), "command": hint["command"]} for hint in self.hints]

    def local_status(self, lang: str = DEFAULT_LANGUAGE) -> dict:
        """Same format as the daemon's "status" response, read-only."""
        data = self.snapshot(lang)
        for fan in data["fans"]:
            fan.update(name=fan["label"], target=None, hidden=False)
        data.update(hints=self.render_hints(lang), failsafe=False, authorized=False)
        return data

    def hottest(self) -> tuple[float, str] | None:
        """Highest temperature among processors and graphics cards."""
        hottest = None
        for temp in self.temps.values():
            if temp.kind not in ("cpu", "gpu"):
                continue
            try:
                value = temp.read()
            except READ_ERRORS:
                continue
            if value is not None and (hottest is None or value > hottest[0]):
                device = self.devices.get(temp.device_id, {}).get("name", temp.device_id)
                hottest = (value, f"{device} / {temp.label}")
        return hottest

    def _compute_hints(self, chips: list[hwmon.HwmonChip]) -> list[dict]:
        hints = []
        dmi = identify.read_dmi(self.sysfs_root)
        has_superio = any(c.kind == "motherboard" and c.pwm_indices for c in chips)
        if not has_superio and not identify.is_laptop(dmi):
            vendor = (dmi.get("board_vendor") or "").lower()
            module = "it87" if "gigabyte" in vendor else "nct6775"
            board = dmi.get("board_name") or Msg("the motherboard")
            if not os.path.isdir(os.path.join(self.sysfs_root, "module", module)):
                hints.append({
                    "text": Msg("Fans connected to {board} are not visible: the {module} driver is not loaded.",
                                board=board, module=module),
                    "command": f"sudo modprobe {module}",
                })
            else:
                hints.append({
                    "text": Msg("The {module} driver is loaded but no motherboard controller was found "
                                "(possible ACPI resource conflict, see the README).", module=module),
                    "command": f"sudo dmesg | grep -iE '{module}|resource conflict'",
                })
        if self._use_nvidia and self._nvml is None and self._nvidia_gpu_present():
            hints.append({
                "text": Msg("NVIDIA graphics card detected but NVML is unavailable ({error}): "
                            "the proprietary NVIDIA driver is required.", error=self._nvml_error),
                "command": None,
            })
        fan_control = os.path.join(self.sysfs_root, "module", "thinkpad_acpi", "parameters", "fan_control")
        if read_str(fan_control) == "N":
            hints.append({
                "text": Msg("ThinkPad fan control is disabled in the thinkpad_acpi module."),
                "command": "echo 'options thinkpad_acpi fan_control=1' | sudo tee /etc/modprobe.d/thinkpad_acpi.conf",
            })
        return hints

    def _nvidia_gpu_present(self) -> bool:
        base = os.path.join(self.sysfs_root, "bus", "pci", "devices")
        try:
            entries = os.listdir(base)
        except OSError:
            return False
        for entry in entries:
            path = os.path.join(base, entry)
            if read_str(os.path.join(path, "vendor")) == "0x10de" and \
                    (read_str(os.path.join(path, "class")) or "").startswith("0x03"):
                return True
        return False
