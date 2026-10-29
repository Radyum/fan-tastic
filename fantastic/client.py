"""Client for the fantasticd socket (used by the GUI and the command line)."""

from __future__ import annotations

import json
import os
import socket

from . import SOCKET_PATH
from .i18n import get_language


class DaemonError(Exception):
    """Error returned by the service."""


class Client:
    def __init__(self, path: str | None = None, timeout: float = 5.0):
        self.path = path or os.environ.get("FANTASTIC_SOCKET", SOCKET_PATH)
        self.timeout = timeout
        self._sock: socket.socket | None = None
        self._file = None

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
        if self._sock is not None:
            self._sock.close()
        self._sock = self._file = None

    def _connect(self) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            sock.connect(self.path)
        except OSError:
            sock.close()
            raise
        self._sock, self._file = sock, sock.makefile("rb")

    def call(self, cmd: str, **params) -> dict:
        """Sends a command; raises OSError if the service is unreachable, DaemonError if it refuses."""
        # Texts in the response (names, hints, errors) come back in the process language.
        payload = json.dumps({"cmd": cmd, "lang": get_language(), **params}).encode() + b"\n"
        for attempt in range(2):
            try:
                if self._sock is None:
                    self._connect()
                self._sock.sendall(payload)
                line = self._file.readline()
                if not line:
                    raise ConnectionError("connection closed by the service")
                break
            except OSError:
                # Stale connection (service restarted): one more attempt.
                self.close()
                if attempt:
                    raise
        response = json.loads(line)
        if not response.get("ok"):
            raise DaemonError(response.get("error", "unknown error"))
        return response
