"""Translations.

English is the source language: every user-facing string in the code is an
English msgid. Other languages map msgids to translations (see
fantastic/translations/); a missing translation falls back to English.

Two ways to translate:
- `_()` and `ngettext()` translate right away into the process language (GUI, CLI);
- `Msg` and `Joined` defer translation: the hardware layer builds them, and the
  daemon renders them in the language each client asks for.
"""

from __future__ import annotations

import os

from .translations import de, es, fr, it

# Language code -> (native name, flag), in menu order
LANGUAGES = {
    "en": ("English", "🇬🇧"),
    "de": ("Deutsch", "🇩🇪"),
    "es": ("Español", "🇪🇸"),
    "fr": ("Français", "🇫🇷"),
    "it": ("Italiano", "🇮🇹"),
}
DEFAULT_LANGUAGE = "en"
CATALOGS = {"de": de.MESSAGES, "es": es.MESSAGES, "fr": fr.MESSAGES, "it": it.MESSAGES}
# Plural rules: does n take the singular form?
SINGULAR = {
    "en": lambda n: n == 1,
    "de": lambda n: n == 1,
    "es": lambda n: n == 1,
    "fr": lambda n: n <= 1,
    "it": lambda n: n == 1,
}

_current = DEFAULT_LANGUAGE


def _code(value: str) -> str:
    """'fr_FR.UTF-8' -> 'fr'."""
    return value.split(".")[0].split("_")[0].split("-")[0].lower()


def normalize(lang) -> str:
    if isinstance(lang, str) and _code(lang) in LANGUAGES:
        return _code(lang)
    return DEFAULT_LANGUAGE


def system_language() -> str:
    """Language from FANTASTIC_LANG, else from the usual locale variables."""
    for var in ("FANTASTIC_LANG", "LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(var)
        if not value:
            continue
        for candidate in value.split(":"):  # LANGUAGE may hold a priority list
            if _code(candidate) in LANGUAGES:
                return _code(candidate)
        if var != "LANGUAGE":
            return DEFAULT_LANGUAGE
    return DEFAULT_LANGUAGE


def set_language(lang) -> None:
    global _current
    _current = normalize(lang)


def get_language() -> str:
    return _current


def render(value, lang: str):
    """Renders Msg and Joined values; anything else is returned unchanged."""
    return value.render(lang) if isinstance(value, (Msg, Joined)) else value


def translate(lang: str, msgid: str, **params) -> str:
    template = CATALOGS.get(lang, {}).get(msgid, msgid)
    if not params:
        return template
    return template.format(**{key: render(value, lang) for key, value in params.items()})


def translate_plural(lang: str, singular: str, plural: str, n: int, **params) -> str:
    entry = CATALOGS.get(lang, {}).get(singular)
    one = SINGULAR.get(lang, SINGULAR[DEFAULT_LANGUAGE])(n)
    if isinstance(entry, tuple):
        template = entry[0] if one else entry[1]
    else:
        template = singular if one else plural
    return template.format(n=n, **{key: render(value, lang) for key, value in params.items()})


def _(msgid: str, **params) -> str:
    return translate(_current, msgid, **params)


def ngettext(singular: str, plural: str, n: int, **params) -> str:
    return translate_plural(_current, singular, plural, n, **params)


class Msg:
    """A message translated later, in the language of whoever displays it."""

    __slots__ = ("msgid", "params")

    def __init__(self, msgid: str, **params):
        self.msgid = msgid
        self.params = params

    def render(self, lang: str) -> str:
        return translate(lang, self.msgid, **self.params)

    def __str__(self) -> str:
        return self.render(DEFAULT_LANGUAGE)

    def __repr__(self) -> str:
        return f"Msg({self.msgid!r}, {self.params!r})"

    def __eq__(self, other) -> bool:
        return isinstance(other, Msg) and (self.msgid, self.params) == (other.msgid, other.params)

    __hash__ = None


class Joined:
    """Parts (str or Msg) joined by a separator once rendered."""

    __slots__ = ("parts", "sep")

    def __init__(self, parts: list, sep: str = " · "):
        self.parts = parts
        self.sep = sep

    def render(self, lang: str) -> str:
        return self.sep.join(render(part, lang) for part in self.parts)

    def __str__(self) -> str:
        return self.render(DEFAULT_LANGUAGE)
