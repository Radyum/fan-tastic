"""NVIDIA graphics card fans through NVML.

NVML (libnvidia-ml.so.1) ships with the proprietary NVIDIA driver. Reading
works for any user; setting fan speeds requires root (and driver 520 or newer).
"""

from __future__ import annotations

import ctypes

from .i18n import Joined, Msg

NVML_SUCCESS = 0
NVML_ERROR_FUNCTION_NOT_FOUND = 13
NVML_FAN_POLICY_MANUAL = 1
NVML_TEMPERATURE_GPU = 0


class NvmlError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


class _PciInfo(ctypes.Structure):
    _fields_ = [
        ("busIdLegacy", ctypes.c_char * 16),
        ("domain", ctypes.c_uint),
        ("bus", ctypes.c_uint),
        ("device", ctypes.c_uint),
        ("pciDeviceId", ctypes.c_uint),
        ("pciSubSystemId", ctypes.c_uint),
        ("busId", ctypes.c_char * 32),
    ]


class _FanSpeedInfo(ctypes.Structure):
    _fields_ = [("version", ctypes.c_uint), ("fan", ctypes.c_uint), ("speed", ctypes.c_uint)]


_FAN_SPEED_INFO_V1 = ctypes.sizeof(_FanSpeedInfo) | (1 << 24)


class Nvml:
    """Minimal ctypes binding to the NVML functions needed for fan control."""

    def __init__(self, library: str = "libnvidia-ml.so.1"):
        try:
            self._lib = ctypes.CDLL(library)
        except OSError as exc:
            raise NvmlError(-1, f"{library} not found") from exc
        self._call("nvmlInit_v2")

    def _call(self, function: str, *args) -> None:
        try:
            fn = getattr(self._lib, function)
        except AttributeError:
            raise NvmlError(NVML_ERROR_FUNCTION_NOT_FOUND, f"{function} missing (driver too old)") from None
        fn.restype = ctypes.c_int
        code = fn(*args)
        if code != NVML_SUCCESS:
            raise NvmlError(code, f"{function} : {self._error_string(code)}")

    def _error_string(self, code: int) -> str:
        fn = self._lib.nvmlErrorString
        fn.restype = ctypes.c_char_p
        fn.argtypes = [ctypes.c_int]
        return fn(code).decode(errors="replace")

    def _uint(self, function: str, *args) -> int:
        value = ctypes.c_uint()
        self._call(function, *args, ctypes.byref(value))
        return value.value

    def _string(self, function: str, handle) -> str:
        buf = ctypes.create_string_buffer(96)
        self._call(function, handle, buf, ctypes.c_uint(len(buf)))
        return buf.value.decode(errors="replace")

    def shutdown(self) -> None:
        self._call("nvmlShutdown")

    def device_count(self) -> int:
        return self._uint("nvmlDeviceGetCount_v2")

    def handle(self, index: int) -> ctypes.c_void_p:
        handle = ctypes.c_void_p()
        self._call("nvmlDeviceGetHandleByIndex_v2", ctypes.c_uint(index), ctypes.byref(handle))
        return handle

    def name(self, handle) -> str:
        return self._string("nvmlDeviceGetName", handle)

    def uuid(self, handle) -> str:
        return self._string("nvmlDeviceGetUUID", handle)

    def pci_bus_id(self, handle) -> str:
        info = _PciInfo()
        self._call("nvmlDeviceGetPciInfo_v3", handle, ctypes.byref(info))
        return info.busId.decode()

    def fan_count(self, handle) -> int:
        return self._uint("nvmlDeviceGetNumFans", handle)

    def fan_speed(self, handle, fan: int) -> int:
        return self._uint("nvmlDeviceGetFanSpeed_v2", handle, ctypes.c_uint(fan))

    def target_fan_speed(self, handle, fan: int) -> int:
        return self._uint("nvmlDeviceGetTargetFanSpeed", handle, ctypes.c_uint(fan))

    def fan_rpm(self, handle, fan: int) -> int:
        info = _FanSpeedInfo(version=_FAN_SPEED_INFO_V1, fan=fan)
        self._call("nvmlDeviceGetFanSpeedRPM", handle, ctypes.byref(info))
        return info.speed

    def fan_speed_range(self, handle) -> tuple[int, int]:
        low, high = ctypes.c_uint(), ctypes.c_uint()
        self._call("nvmlDeviceGetMinMaxFanSpeed", handle, ctypes.byref(low), ctypes.byref(high))
        return low.value, high.value

    def fan_policy(self, handle, fan: int) -> int:
        return self._uint("nvmlDeviceGetFanControlPolicy_v2", handle, ctypes.c_uint(fan))

    def set_fan_speed(self, handle, fan: int, percent: int) -> None:
        self._call("nvmlDeviceSetFanSpeed_v2", handle, ctypes.c_uint(fan), ctypes.c_uint(percent))

    def set_default_fan_speed(self, handle, fan: int) -> None:
        self._call("nvmlDeviceSetDefaultFanSpeed_v2", handle, ctypes.c_uint(fan))

    def temperature(self, handle) -> int:
        return self._uint("nvmlDeviceGetTemperature", handle, ctypes.c_int(NVML_TEMPERATURE_GPU))


def _short_bus_id(bus_id: str) -> str:
    """'00000000:09:00.0' -> '0000:09:00.0' (sysfs format)."""
    domain, _, rest = bus_id.lower().partition(":")
    return f"{domain[-4:]}:{rest}"


# Calibration: NVIDIA cards refuse less than their minimum (30% on a 3080) and their fans
# only start spinning at some higher duty ("start percent", about 43% measured on a 3080).
# With a start percent, the user-facing scale is remapped: logical 5% is the lowest speed at
# which the fans really spin, and logical 0-5% covers the range where they are stopped.
STOP_BELOW = 5  # logical percent under which the fans are stopped


def to_raw(percent: int, low: int, start: int | None) -> int:
    """Logical percent -> NVML percent."""
    if start is None:
        return percent
    if percent >= STOP_BELOW:
        return round(start + (percent - STOP_BELOW) * (100 - start) / (100 - STOP_BELOW))
    return round(low + percent * (start - low) / STOP_BELOW)


def to_logical(raw: int, low: int, start: int | None) -> int:
    """NVML percent -> logical percent (inverse of to_raw)."""
    if start is None:
        return raw
    if raw >= start:
        return round(STOP_BELOW + (raw - start) * (100 - STOP_BELOW) / (100 - start))
    return max(0, round((raw - low) * STOP_BELOW / (start - low)))


class NvidiaGpu:
    def __init__(self, nvml: Nvml, index: int, start_percent: int | None = None):
        self.nvml = nvml
        self.handle = nvml.handle(index)
        self.name = nvml.name(self.handle)
        try:
            self.address = _short_bus_id(nvml.pci_bus_id(self.handle))
            self.id = f"nvidia@pci-{self.address}"
        except NvmlError:
            self.address = None
            self.id = f"nvidia@{nvml.uuid(self.handle)}"
        try:
            self.fan_count = nvml.fan_count(self.handle)
        except NvmlError:
            self.fan_count = 0
        try:
            self.min_percent, self.max_percent = nvml.fan_speed_range(self.handle)
        except NvmlError:
            self.min_percent, self.max_percent = 0, 100
        usable = start_percent is not None and self.min_percent < start_percent < 100
        self.start_percent = start_percent if usable else None

    def device_info(self) -> dict:
        details = [f"PCI {self.address}"] if self.address else []
        details.append(Msg("NVIDIA driver (NVML)"))
        return {"id": self.id, "name": self.name, "kind": "gpu", "driver": "nvidia",
                "details": Joined(details)}

    def fans(self) -> list[NvidiaFan]:
        return [NvidiaFan(self, i) for i in range(self.fan_count)]

    def temps(self) -> list[NvidiaTemp]:
        try:
            self.nvml.temperature(self.handle)
        except NvmlError:
            return []
        return [NvidiaTemp(self)]


class NvidiaFan:
    controllable = True

    def __init__(self, gpu: NvidiaGpu, index: int):
        self.gpu = gpu
        self.index = index
        self.channel = f"fan{index}"
        self.id = f"{gpu.id}/{self.channel}"
        self.device_id = gpu.id
        self.label = Msg("Fan {n}", n=index + 1)
        # With calibration, the whole 0-100% scale is usable (below 5% the fans stop).
        self.min_percent = 0 if gpu.start_percent else gpu.min_percent
        self.stop_below = STOP_BELOW if gpu.start_percent else None

    def _raw(self, percent: int) -> int:
        return to_raw(percent, self.gpu.min_percent, self.gpu.start_percent)

    def read(self) -> dict:
        nvml, handle = self.gpu.nvml, self.gpu.handle
        try:
            rpm = nvml.fan_rpm(handle, self.index)
        except NvmlError:
            rpm = None
        try:
            mode = "manual" if nvml.fan_policy(handle, self.index) == NVML_FAN_POLICY_MANUAL else "auto"
        except NvmlError:
            mode = "unknown"
        return {"rpm": rpm, "percent": to_logical(nvml.fan_speed(handle, self.index), self.gpu.min_percent,
                                        self.gpu.start_percent),
                "mode": mode}

    def control_state(self) -> None:
        return None  # NVML restores automatic mode on its own

    def apply(self, percent: int) -> None:
        self.gpu.nvml.set_fan_speed(self.gpu.handle, self.index, self._raw(percent))

    def is_applied(self, percent: int) -> bool:
        nvml, handle = self.gpu.nvml, self.gpu.handle
        try:
            if nvml.fan_policy(handle, self.index) != NVML_FAN_POLICY_MANUAL:
                return False
        except NvmlError:
            pass
        return nvml.target_fan_speed(handle, self.index) == self._raw(percent)

    def restore(self, original: None) -> None:
        self.gpu.nvml.set_default_fan_speed(self.gpu.handle, self.index)


class NvidiaTemp:
    kind = "gpu"
    label = "GPU"
    index = 0

    def __init__(self, gpu: NvidiaGpu):
        self.gpu = gpu
        self.id = f"{gpu.id}/temp"
        self.device_id = gpu.id

    def read(self) -> float | None:
        try:
            return float(self.gpu.nvml.temperature(self.gpu.handle))
        except NvmlError:
            return None


def scan(nvml: Nvml, start_percent: int | None = None) -> list[NvidiaGpu]:
    return [NvidiaGpu(nvml, i, start_percent) for i in range(nvml.device_count())]
