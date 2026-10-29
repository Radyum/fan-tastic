"""Number formatting in the current language."""

from __future__ import annotations

from .i18n import _, get_language

NBSP = " "
NNBSP = " "
# Language -> (thousands separator, decimal separator)
SEPARATORS = {"en": (",", "."), "de": (".", ","), "es": (".", ","), "fr": (NNBSP, ","), "it": (".", ",")}


def _separators() -> tuple[str, str]:
    return SEPARATORS.get(get_language(), SEPARATORS["en"])


def fmt_int(value: int) -> str:
    return f"{value:,}".replace(",", _separators()[0])


def fmt_rpm(rpm: int | None) -> str:
    return "—" if rpm is None else _("{value} RPM", value=fmt_int(rpm))


def fmt_percent(percent: int | None) -> str:
    return "—" if percent is None else _("{value}%", value=percent)


def fmt_temp(celsius: float | None) -> str:
    if celsius is None:
        return "—"
    return f"{celsius:.1f}".replace(".", _separators()[1]) + f"{NBSP}°C"
