import ast
import os
import pathlib
import string
import unittest
from unittest import mock

from fantastic import i18n
from fantastic.fmt import fmt_percent, fmt_rpm, fmt_temp
from fantastic.i18n import Joined, Msg, render

PACKAGE = pathlib.Path(__file__).resolve().parent.parent / "fantastic"
NBSP, NNBSP = " ", " "


def code_msgids() -> dict[str, str | None]:
    """msgid -> plural msgid (None for simple messages), for every _(), ngettext() and Msg() of the package."""
    found = {}
    for path in PACKAGE.rglob("*.py"):
        if "translations" in path.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", None)
            if name in ("_", "Msg", "ngettext") and node.args and isinstance(node.args[0], ast.Constant):
                plural = node.args[1].value if name == "ngettext" else None
                found[node.args[0].value] = plural
    return found


def placeholders(template: str) -> set[str]:
    return {field for _text, field, _spec, _conv in string.Formatter().parse(template) if field}


class CatalogTest(unittest.TestCase):
    def test_every_language_is_wired(self):
        self.assertEqual(set(i18n.CATALOGS) | {i18n.DEFAULT_LANGUAGE}, set(i18n.LANGUAGES))
        self.assertEqual(set(i18n.SINGULAR), set(i18n.LANGUAGES))

    def test_every_message_is_translated(self):
        msgids = set(code_msgids())
        for lang, catalog in i18n.CATALOGS.items():
            with self.subTest(lang=lang):
                missing = sorted(msgids - set(catalog))
                self.assertEqual(missing, [], f"add these msgids to fantastic/translations/{lang}.py")

    def test_no_stale_translation(self):
        msgids = set(code_msgids())
        for lang, catalog in i18n.CATALOGS.items():
            with self.subTest(lang=lang):
                stale = sorted(set(catalog) - msgids)
                self.assertEqual(stale, [], "these msgids are no longer used in the code")

    def test_forms_and_placeholders_match(self):
        for lang, catalog in i18n.CATALOGS.items():
            for msgid, plural in code_msgids().items():
                translation = catalog.get(msgid)
                if translation is None:
                    continue
                with self.subTest(lang=lang, msgid=msgid):
                    if plural is None:
                        self.assertIsInstance(translation, str)
                        self.assertEqual(placeholders(translation), placeholders(msgid))
                    else:
                        self.assertIsInstance(translation, tuple)
                        for form in translation:
                            self.assertEqual(placeholders(form), placeholders(plural) | {"n"})


class RenderingTest(unittest.TestCase):
    def tearDown(self):
        i18n.set_language("en")

    def test_deferred_messages(self):
        name = Joined([Msg("Motherboard ({chip})", chip="Nuvoton NCT6798"), "X"], sep=" ")
        self.assertEqual(render(name, "en"), "Motherboard (Nuvoton NCT6798) X")
        self.assertEqual(render(name, "fr"), "Carte mère (Nuvoton NCT6798) X")
        self.assertEqual(render(name, "de"), "Mainboard (Nuvoton NCT6798) X")
        self.assertEqual(str(Msg("Fan {n}", n=2)), "Fan 2")
        self.assertEqual(render("plain text", "fr"), "plain text")

    def test_plurals(self):
        expected = {
            "en": ("0 fans", "1 fan", "2 fans"),
            "fr": ("0 ventilateur", "1 ventilateur", "2 ventilateurs"),
            "es": ("0 ventiladores", "1 ventilador", "2 ventiladores"),
            "it": ("0 ventole", "1 ventola", "2 ventole"),
        }
        for lang, forms in expected.items():
            i18n.set_language(lang)
            with self.subTest(lang=lang):
                self.assertEqual(tuple(i18n.ngettext("{n} fan", "{n} fans", n) for n in (0, 1, 2)), forms)

    def test_unknown_language_falls_back_to_english(self):
        i18n.set_language("pt")
        self.assertEqual(i18n.get_language(), "en")
        self.assertEqual(i18n._("Pump"), "Pump")

    def test_system_language(self):
        cases = [
            ({"LANG": "fr_FR.UTF-8"}, "fr"),
            ({"LANG": "de_DE.UTF-8"}, "de"),
            ({"LANG": "pt_BR.UTF-8"}, "en"),
            ({"LANGUAGE": "pt:it", "LANG": "pt_BR.UTF-8"}, "it"),
            ({"LC_ALL": "C", "LANG": "fr_FR.UTF-8"}, "en"),
            ({"FANTASTIC_LANG": "es", "LANG": "en_US.UTF-8"}, "es"),
            ({}, "en"),
        ]
        for env, expected in cases:
            with self.subTest(env=env), mock.patch.dict(os.environ, env, clear=True):
                self.assertEqual(i18n.system_language(), expected)

    def test_number_formatting(self):
        expected = {
            "en": ("1,045 RPM", "30%", f"45.2{NBSP}°C"),
            "fr": (f"1{NNBSP}045{NBSP}tr/min", f"30{NBSP}%", f"45,2{NBSP}°C"),
            "de": (f"1.045{NBSP}U/min", f"30{NBSP}%", f"45,2{NBSP}°C"),
            "es": (f"1.045{NBSP}rpm", f"30{NBSP}%", f"45,2{NBSP}°C"),
            "it": (f"1.045{NBSP}giri/min", "30%", f"45,2{NBSP}°C"),
        }
        for lang, values in expected.items():
            i18n.set_language(lang)
            with self.subTest(lang=lang):
                self.assertEqual((fmt_rpm(1045), fmt_percent(30), fmt_temp(45.25)), values)


if __name__ == "__main__":
    unittest.main()
