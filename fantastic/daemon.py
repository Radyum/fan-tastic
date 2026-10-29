"""fantasticd: root service that applies fan speed targets.

It listens on a Unix socket (one JSON request per line, one JSON response per
line), stores targets in a state file, reapplies them when the hardware loses
them (suspend, USB reconnection) and hands control back to the hardware's
automatic mode when it stops.

Texts in responses are rendered in the language requested by each client
("lang" field, English by default); logs are in English.
"""

from __future__ import annotations

import argparse
import grp
import json
import logging
import os
import pwd
import signal
import socket
import socketserver
import struct
import threading
import time

from . import CONFIG_PATH, SOCKET_PATH, STATE_PATH, __version__
from .hardware import READ_ERRORS, Hardware
from .i18n import DEFAULT_LANGUAGE, Msg, normalize, render

log = logging.getLogger("fantasticd")

DEFAULT_CONFIG = {
    # Who may change speeds (root always may; reading is open to everyone).
    "allowed_users": [],
    "allowed_groups": ["sudo", "wheel", "admin", "fantastic"],
    # Thermal failsafe: above this CPU/GPU temperature (°C), manually driven fans
    # go to 100%. null disables it.
    "failsafe_temp": 90,
    "failsafe_hysteresis": 10,
    "poll_interval": 2,
    "rescan_interval": 15,
    "nvidia": True,
}

WRITE_COMMANDS = {"set", "set_all", "auto", "auto_all", "rename", "hide", "unhide_all", "rescan"}
MAX_REQUEST = 64 * 1024


class ServiceError(Exception):
    """Error reported to the client, translated into its language."""

    def __init__(self, message: str | Msg):
        super().__init__(str(message))
        self.message = message

    def render(self, lang: str) -> str:
        return render(self.message, lang)


def load_config(path: str) -> dict:
    config = dict(DEFAULT_CONFIG)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return config
    except (OSError, ValueError) as exc:
        log.error("unreadable configuration %s (%s): using defaults", path, exc)
        return config
    for key in data.keys() - config.keys():
        log.warning("unknown option ignored in %s: %s", path, key)
    config.update((k, v) for k, v in data.items() if k in config)
    return config


def describe_error(exc: Exception) -> str | Msg:
    if isinstance(exc, PermissionError):
        return Msg("permission denied on {path} (the service must run as root)", path=exc.filename)
    if isinstance(exc, OSError) and exc.filename:
        return f"{exc.strerror} ({exc.filename})"
    return str(exc)


def is_authorized(uid: int, config: dict) -> bool:
    if uid == 0:
        return True
    try:
        user = pwd.getpwuid(uid)
    except KeyError:
        return False
    if user.pw_name in config["allowed_users"]:
        return True
    # The group database is read on every connection: joining a group takes
    # effect without logging out.
    groups = set(os.getgrouplist(user.pw_name, user.pw_gid))
    for name in config["allowed_groups"]:
        try:
            if grp.getgrnam(name).gr_gid in groups:
                return True
        except KeyError:
            continue
    return False


class FanService:
    def __init__(self, hardware: Hardware, config: dict, state_path: str):
        self.hw = hardware
        self.config = config
        self.state_path = state_path
        self.lock = threading.RLock()
        self.failsafe = False
        self.errors: dict[str, str | Msg] = {}
        self.targets: dict[str, int] = {}
        self.originals: dict[str, int] = {}
        self.names: dict[str, str] = {}
        self.hidden: set[str] = set()
        self._load_state()

    # --- persistent state --------------------------------------------------

    def _load_state(self) -> None:
        try:
            with open(self.state_path, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            return
        except (OSError, ValueError) as exc:
            log.error("unreadable state %s (%s): ignored", self.state_path, exc)
            return
        self.targets = {k: int(v) for k, v in data.get("targets", {}).items()}
        self.originals = {k: int(v) for k, v in data.get("originals", {}).items()}
        self.names = {k: str(v) for k, v in data.get("names", {}).items()}
        self.hidden = {str(v) for v in data.get("hidden", [])}

    def _save_state(self) -> None:
        data = {"targets": self.targets, "originals": self.originals, "names": self.names,
                "hidden": sorted(self.hidden)}
        tmp = self.state_path + ".tmp"
        try:
            os.makedirs(os.path.dirname(self.state_path) or ".", exist_ok=True)
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.state_path)
        except OSError as exc:
            log.error("cannot save state: %s", describe_error(exc))

    # --- commands ----------------------------------------------------------

    def dispatch(self, request: dict, authorized: bool, lang: str = DEFAULT_LANGUAGE) -> dict:
        cmd = request.get("cmd")
        if cmd == "status":
            return {"ok": True, "authorized": authorized, **self.status(lang)}
        if cmd not in WRITE_COMMANDS:
            raise ServiceError(Msg("unknown command: {cmd}", cmd=cmd))
        if not authorized:
            raise ServiceError(Msg("not authorized: add your user to allowed_users in /etc/fantastic/config.json"))
        if cmd == "rescan":
            self.rescan()
            return {"ok": True}
        if cmd == "set_all":
            applied, errors = self.set_all(request.get("percent"))
            return {"ok": True, "applied": applied, "errors": self._render_errors(errors, lang)}
        if cmd == "auto_all":
            return {"ok": True, "errors": self._render_errors(self.auto_all(), lang)}
        if cmd == "unhide_all":
            return {"ok": True, "count": self.unhide_all()}
        fan_id = request.get("fan")
        if not isinstance(fan_id, str):
            raise ServiceError(Msg("missing 'fan' parameter"))
        if cmd == "set":
            return {"ok": True, "applied": self.set_speed(fan_id, request.get("percent"))}
        if cmd == "auto":
            self.set_auto(fan_id)
        elif cmd == "hide":
            self.set_hidden(fan_id, request.get("hidden", True))
        else:
            self.rename(fan_id, request.get("name"))
        return {"ok": True}

    @staticmethod
    def _render_errors(errors: dict[str, ServiceError], lang: str) -> dict[str, str]:
        return {fan_id: exc.render(lang) for fan_id, exc in errors.items()}

    def status(self, lang: str = DEFAULT_LANGUAGE) -> dict:
        with self.lock:
            data = self.hw.snapshot(lang)
            for fan in data["fans"]:
                fan["name"] = self.names.get(fan["id"]) or fan["label"]
                fan["target"] = self.targets.get(fan["id"])
                fan["hidden"] = fan["id"] in self.hidden
                if fan["id"] in self.errors:
                    fan["error"] = render(self.errors[fan["id"]], lang)
            data.update(hints=self.hw.render_hints(lang), failsafe=self.failsafe,
                        failsafe_temp=self.config.get("failsafe_temp"), version=__version__)
            return data

    def set_speed(self, fan_id: str, percent) -> int:
        try:
            value = round(float(percent))
        except (TypeError, ValueError):
            raise ServiceError(Msg("invalid 'percent' parameter")) from None
        with self.lock:
            fan = self._controllable_fan(fan_id)
            value = max(fan.min_percent, min(100, value))
            self.targets[fan_id] = value
            self._save_state()
            self._enforce(fan, force=True)
            return value

    def set_auto(self, fan_id: str) -> None:
        with self.lock:
            fan = self._controllable_fan(fan_id)
            if self.targets.pop(fan_id, None) is not None:
                self._save_state()
            self.errors.pop(fan_id, None)
            try:
                fan.restore(self.originals.get(fan_id))
            except READ_ERRORS as exc:
                raise ServiceError(describe_error(exc)) from exc

    def set_all(self, percent) -> tuple[dict[str, int], dict[str, ServiceError]]:
        """Same target for every controllable, visible fan (bounded by each fan's minimum)."""
        applied, errors = {}, {}
        with self.lock:
            for fan in self.hw.fans.values():
                if not fan.controllable or fan.id in self.hidden:
                    continue
                try:
                    applied[fan.id] = self.set_speed(fan.id, percent)
                except ServiceError as exc:
                    errors[fan.id] = exc
        return applied, errors

    def auto_all(self) -> dict[str, ServiceError]:
        """Hands every manually driven fan back to automatic control, hidden ones included."""
        errors = {}
        with self.lock:
            for fan in self.hw.fans.values():
                if not fan.controllable:
                    continue
                if fan.id not in self.targets:
                    try:
                        if fan.read()["mode"] != "manual":
                            continue
                    except READ_ERRORS:
                        continue
                try:
                    self.set_auto(fan.id)
                except ServiceError as exc:
                    errors[fan.id] = exc
        return errors

    def set_hidden(self, fan_id: str, hidden) -> None:
        """Hides a fan from display, without changing its setting."""
        if not isinstance(hidden, bool):
            raise ServiceError(Msg("invalid 'hidden' parameter"))
        with self.lock:
            if fan_id not in self.hw.fans:
                raise ServiceError(Msg("unknown fan: {fan}", fan=fan_id))
            if hidden:
                self.hidden.add(fan_id)
            else:
                self.hidden.discard(fan_id)
            self._save_state()

    def unhide_all(self) -> int:
        with self.lock:
            count = len(self.hidden)
            self.hidden.clear()
            self._save_state()
            return count

    def rename(self, fan_id: str, name) -> None:
        if name is not None and not isinstance(name, str):
            raise ServiceError(Msg("invalid 'name' parameter"))
        name = (name or "").strip()[:64]
        with self.lock:
            if fan_id not in self.hw.fans:
                raise ServiceError(Msg("unknown fan: {fan}", fan=fan_id))
            if name:
                self.names[fan_id] = name
            else:
                self.names.pop(fan_id, None)
            self._save_state()

    def rescan(self) -> None:
        with self.lock:
            self.hw.scan()
        self.tick()

    # --- monitoring loop ---------------------------------------------------

    def tick(self) -> None:
        """Checks the thermal failsafe and reapplies lost targets."""
        with self.lock:
            self._update_failsafe()
            for fan_id in list(self.targets):
                fan = self.hw.fans.get(fan_id)
                if fan is not None and fan.controllable:
                    self._enforce(fan)

    def restore_all(self) -> None:
        with self.lock:
            for fan_id in self.targets:
                fan = self.hw.fans.get(fan_id)
                if fan is None:
                    continue
                try:
                    fan.restore(self.originals.get(fan_id))
                    log.info("%s: back to automatic mode", fan_id)
                except READ_ERRORS as exc:
                    log.error("%s: cannot restore automatic mode: %s", fan_id, describe_error(exc))

    def _controllable_fan(self, fan_id: str):
        fan = self.hw.fans.get(fan_id)
        if fan is None:
            raise ServiceError(Msg("unknown fan: {fan}", fan=fan_id))
        if not fan.controllable:
            raise ServiceError(Msg("{fan} is read-only", fan=fan_id))
        return fan

    def _enforce(self, fan, force: bool = False) -> None:
        desired = 100 if self.failsafe else self.targets[fan.id]
        try:
            if force or not fan.is_applied(desired):
                self._remember_original(fan)
                fan.apply(desired)
                log.debug("%s: %d%%", fan.id, desired)
            self.errors.pop(fan.id, None)
        except READ_ERRORS as exc:
            message = describe_error(exc)
            if self.errors.get(fan.id) != message:
                log.error("%s: %s", fan.id, message)
            self.errors[fan.id] = message
            if force:
                raise ServiceError(message) from exc

    def _remember_original(self, fan) -> None:
        # Remember the original automatic mode (pwmN_enable) before switching to
        # manual, so it can be restored even after the service restarts.
        state = fan.control_state()
        if state is not None and state != 1 and self.originals.get(fan.id) != state:
            self.originals[fan.id] = state
            self._save_state()

    def _update_failsafe(self) -> None:
        limit = self.config.get("failsafe_temp")
        if not limit:
            self.failsafe = False
            return
        hottest = self.hw.hottest()
        if not self.failsafe and hottest and hottest[0] >= limit:
            self.failsafe = True
            log.warning("thermal failsafe: %s at %.0f °C, driven fans set to 100%%", hottest[1], hottest[0])
        elif self.failsafe and (hottest is None or hottest[0] < limit - self.config["failsafe_hysteresis"]):
            self.failsafe = False
            log.info("thermal failsafe cleared, back to targets")


def peer_uid(sock: socket.socket) -> int:
    creds = sock.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
    _pid, uid, _gid = struct.unpack("3i", creds)
    return uid


class _Handler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        service: FanService = self.server.service
        authorized = is_authorized(peer_uid(self.request), service.config)
        while line := self.rfile.readline(MAX_REQUEST):
            lang = DEFAULT_LANGUAGE
            try:
                request = json.loads(line)
                if not isinstance(request, dict):
                    raise ValueError
                lang = normalize(request.get("lang"))
                response = service.dispatch(request, authorized, lang)
            except ServiceError as exc:
                response = {"ok": False, "error": exc.render(lang)}
            except ValueError:
                response = {"ok": False, "error": render(Msg("invalid request"), lang)}
            except Exception as exc:  # a request must never bring the service down
                log.exception("internal error")
                response = {"ok": False, "error": render(Msg("internal error: {error}", error=str(exc)), lang)}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode() + b"\n")


class _Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True

    def __init__(self, path: str, service: FanService):
        self.service = service
        super().__init__(path, _Handler)


def make_server(path: str, service: FanService) -> _Server:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if os.path.exists(path):
        os.unlink(path)
    server = _Server(path, service)
    # The socket is open to everyone: reading is free, writes are filtered
    # by the client's identity (SO_PEERCRED).
    os.chmod(path, 0o666)
    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fantastic daemon", description="Fan control service.")
    parser.add_argument("--socket", default=SOCKET_PATH, help=f"Unix socket (default: {SOCKET_PATH})")
    parser.add_argument("--config", default=CONFIG_PATH, help=f"configuration (default: {CONFIG_PATH})")
    parser.add_argument("--state", default=STATE_PATH, help=f"state file (default: {STATE_PATH})")
    parser.add_argument("--sysfs-root", default="/sys", help="sysfs root (tests)")
    parser.add_argument("--no-nvidia", action="store_true", help="ignore NVIDIA cards")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")
    config = load_config(args.config)
    if os.geteuid() != 0:
        log.warning("the service is not running as root: setting fan speeds will probably fail")

    hardware = Hardware(sysfs_root=args.sysfs_root, use_nvidia=config["nvidia"] and not args.no_nvidia)
    service = FanService(hardware, config, args.state)
    controllable = sum(1 for fan in hardware.fans.values() if fan.controllable)
    log.info("fantasticd %s: %d fan(s) detected, %d controllable", __version__, len(hardware.fans), controllable)
    for hint in hardware.hints:
        log.info("hint: %s", hint["text"])

    server = make_server(args.socket, service)
    stop = threading.Event()

    def reload_config(*_args):
        service.config = load_config(args.config)
        log.info("configuration reloaded")

    signal.signal(signal.SIGTERM, lambda *_args: stop.set())
    signal.signal(signal.SIGINT, lambda *_args: stop.set())
    signal.signal(signal.SIGHUP, reload_config)
    threading.Thread(target=server.serve_forever, name="socket", daemon=True).start()

    try:
        service.tick()
        last_scan = time.monotonic()
        while not stop.wait(service.config["poll_interval"]):
            if time.monotonic() - last_scan >= service.config["rescan_interval"]:
                service.rescan()
                last_scan = time.monotonic()
            else:
                service.tick()
    finally:
        server.shutdown()
        server.server_close()
        try:
            os.unlink(args.socket)
        except OSError:
            pass
        service.restore_all()
        hardware.close()
        log.info("stopped")
    return 0
