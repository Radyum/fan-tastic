"""Command line: fantastic [list|set|auto|rename|hide|unhide|detect|gui|daemon].

Messages follow the system language (FANTASTIC_LANG, LANGUAGE, LC_ALL, LANG).
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__, i18n
from .client import Client, DaemonError
from .fmt import fmt_percent, fmt_rpm, fmt_temp
from .hardware import Hardware
from .i18n import _, ngettext


class CliError(Exception):
    pass


def mode_text(fan: dict, failsafe: bool) -> str:
    if not fan["controllable"]:
        return _("read-only")
    if fan.get("target") is not None:
        return _("failsafe 100%") if failsafe else _("manual {value}", value=fmt_percent(fan["target"]))
    return {"manual": _("manual"), "auto": _("auto")}.get(fan.get("mode"), "?")


def percent_arg(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(_("'{value}' is not an integer", value=text)) from None
    if not 0 <= value <= 100:
        raise argparse.ArgumentTypeError(_("the value must be between 0 and 100"))
    return value


def print_table(rows: list[tuple], right: set[int] = frozenset()) -> None:
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    for n, row in enumerate(rows):
        cells = [cell.rjust(w) if i in right else cell.ljust(w) for i, (cell, w) in enumerate(zip(row, widths))]
        print("  ".join(cells).rstrip())
        if n == 0:
            print("  ".join("─" * w for w in widths))


def print_hints(hints: list[dict]) -> None:
    for hint in hints:
        print(f"\n💡 {hint['text']}")
        if hint.get("command"):
            print(f"   {hint['command']}")


def get_status() -> tuple[dict, bool]:
    """Asks the service; otherwise reads the hardware directly (without being able to drive it)."""
    try:
        return Client().call("status"), True
    except OSError as exc:
        print(_("fantasticd service unreachable ({error}): reading the hardware directly.", error=exc) + "\n",
              file=sys.stderr)
    hardware = Hardware()
    try:
        return hardware.local_status(i18n.get_language()), False
    finally:
        hardware.close()


def resolve_fan(fans: list[dict], ref: str) -> dict:
    """Accepts the number shown by "fantastic list", the identifier or an unambiguous part of the name."""
    if ref.isdigit() and 1 <= int(ref) <= len(fans):
        return fans[int(ref) - 1]
    for fan in fans:
        if fan["id"] == ref:
            return fan
    needle = ref.lower()
    matches = [f for f in fans if needle in f["id"].lower() or needle in f["name"].lower()]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise CliError(_("no fan matches '{ref}' (see \"fantastic list\")", ref=ref))
    raise CliError(_("'{ref}' is ambiguous: {matches}", ref=ref, matches=", ".join(f["id"] for f in matches)))


def cmd_list(args) -> int:
    data, _live = get_status()
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0
    devices = {d["id"]: d for d in data["devices"]}
    rows = [("#", _("Name"), _("Device"), _("Speed"), _("Duty"), _("Mode"), _("Identifier"))]
    hidden = 0
    # Numbering covers every fan, hidden ones included, to stay consistent with "fantastic set N".
    for n, fan in enumerate(data["fans"], 1):
        mode = mode_text(fan, data["failsafe"])
        if fan.get("hidden"):
            hidden += 1
            if not args.all:
                continue
            mode = _("{mode} (hidden)", mode=mode)
        rows.append((str(n), fan["name"], devices[fan["device_id"]]["name"], fmt_rpm(fan["rpm"]),
                     fmt_percent(fan["percent"]), mode, fan["id"]))
    if len(rows) > 1:
        print_table(rows, right={0, 3, 4})
    elif not data["fans"]:
        print(_("No fan detected."))
    if hidden and not args.all:
        print("\n" + ngettext("{n} hidden fan: \"fantastic list --all\" shows it.",
                              "{n} hidden fans: \"fantastic list --all\" shows them.", hidden))
    if args.temps:
        print()
        rows = [(_("Sensor"), _("Device"), _("Temperature"))]
        for temp in data["temps"]:
            rows.append((temp["label"], devices[temp["device_id"]]["name"], fmt_temp(temp["celsius"])))
        print_table(rows, right={2})
    if data.get("failsafe"):
        print("\n⚠ " + _("Thermal failsafe active (threshold {temp} °C): driven fans forced to 100%.",
                         temp=data.get("failsafe_temp")))
    print_hints(data["hints"])
    return 0


def cmd_detect(args) -> int:
    hardware = Hardware()
    try:
        data = hardware.local_status(i18n.get_language())
    finally:
        hardware.close()
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0
    for device in data["devices"]:
        print(f"{device['name']}  [{device['kind']}]")
        print(f"  {device['details']}")
        print(f"  id: {device['id']}")
        items = []
        for fan in (f for f in data["fans"] if f["device_id"] == device["id"]):
            state = _("controllable") if fan["controllable"] else _("read-only")
            if fan["min_percent"]:
                state += ", " + _("min. {value}", value=fmt_percent(fan["min_percent"]))
            reading = fmt_rpm(fan["rpm"])
            if fan["controllable"]:
                reading += f", {fmt_percent(fan['percent'])} ({fan['mode']})"
            items.append(_("Fan '{label}' ({channel}): {reading} — {state}",
                           label=fan["label"], channel=fan["channel"], reading=reading, state=state))
        for temp in (t for t in data["temps"] if t["device_id"] == device["id"]):
            items.append(_("Temperature '{label}': {value}", label=temp["label"], value=fmt_temp(temp["celsius"])))
        for i, item in enumerate(items):
            print(f"  {'└' if i == len(items) - 1 else '├'} {item}")
        print()
    print_hints(data["hints"])
    return 0


def print_errors(fans: list[dict], errors: dict[str, str]) -> int:
    names = {f["id"]: f["name"] for f in fans}
    for fan_id, message in errors.items():
        print(_("Error on {fan}: {error}", fan=names.get(fan_id, fan_id), error=message), file=sys.stderr)
    return 1 if errors else 0


def warn_stop(fan: dict, percent: int) -> None:
    if fan.get("stop_below") and percent < fan["stop_below"]:
        print("⚠ " + _("Warning: below {value} the fan stops spinning.", value=fmt_percent(fan["stop_below"])),
              file=sys.stderr)


def cmd_set(args) -> int:
    client = Client()
    fans = client.call("status")["fans"]
    if args.fan == "all":
        response = client.call("set_all", percent=args.percent)
        names = {f["id"]: f["name"] for f in fans}
        for fan_id, value in response["applied"].items():
            print(f"{names.get(fan_id, fan_id)}: {fmt_percent(value)}")
            warn_stop(next(f for f in fans if f["id"] == fan_id), value)
        return print_errors(fans, response["errors"])
    fan = resolve_fan(fans, args.fan)
    response = client.call("set", fan=fan["id"], percent=args.percent)
    print(f"{fan['name']}: {fmt_percent(response['applied'])}")
    warn_stop(fan, response["applied"])
    return 0


def cmd_auto(args) -> int:
    client = Client()
    fans = client.call("status")["fans"]
    if args.fan == "all":
        return print_errors(fans, client.call("auto_all")["errors"])
    fan = resolve_fan(fans, args.fan)
    client.call("auto", fan=fan["id"])
    print(f"{fan['name']}: {_('automatic')}")
    return 0


def cmd_rename(args) -> int:
    client = Client()
    fan = resolve_fan(client.call("status")["fans"], args.fan)
    client.call("rename", fan=fan["id"], name=args.name or "")
    print(f"{fan['id']}: {args.name or _('original name')}")
    return 0


def cmd_hide(args) -> int:
    client = Client()
    fan = resolve_fan(client.call("status")["fans"], args.fan)
    client.call("hide", fan=fan["id"], hidden=True)
    print(f"{fan['name']}: {_('hidden')}")
    return 0


def cmd_unhide(args) -> int:
    client = Client()
    if args.fan == "all":
        count = client.call("unhide_all")["count"]
        print(ngettext("{n} fan shown again", "{n} fans shown again", count))
        return 0
    fan = resolve_fan(client.call("status")["fans"], args.fan)
    client.call("hide", fan=fan["id"], hidden=False)
    print(f"{fan['name']}: {_('shown again')}")
    return 0


def cmd_profile(args) -> int:
    client = Client()
    if args.action == "list":
        names = client.call("status")["profiles"]
        print("\n".join(names) if names else _("No profile."))
    elif args.action == "save":
        client.call("profile_save", name=args.name)
        print(_("Profile '{name}' saved", name=args.name))
    elif args.action == "delete":
        client.call("profile_delete", name=args.name)
        print(_("Profile '{name}' deleted", name=args.name))
    else:
        errors = client.call("profile_apply", name=args.name)["errors"]
        print(_("Profile '{name}' applied", name=args.name))
        return print_errors(client.call("status")["fans"], errors)
    return 0


def cmd_gui(_args) -> int:
    try:
        from . import gui
    except (ImportError, ValueError) as exc:
        raise CliError(_("graphical interface unavailable ({error}).", error=exc) + "\n"
                       + _("Install: {command}", command="sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1")
                       ) from exc
    return gui.main()


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["daemon"]:
        from . import daemon
        return daemon.main(argv[1:])

    i18n.set_language(i18n.system_language())
    parser = argparse.ArgumentParser(prog="fantastic", description=_("Fan detection and control."))
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="command")

    p = sub.add_parser("list", help=_("list fans (default command)"))
    p.add_argument("-t", "--temps", action="store_true", help=_("also show temperatures"))
    p.add_argument("-a", "--all", action="store_true", help=_("include hidden fans"))
    p.add_argument("--json", action="store_true", help=_("JSON output"))
    p.set_defaults(func=cmd_list)

    # argparse formats help strings with %: the percent sign must be doubled.
    p = sub.add_parser("set", help=_("set the speed of a fan, or of all visible ones with 'all' (0-100%)")
                       .replace("%", "%%"))
    p.add_argument("fan", help=_("number, identifier or name of the fan, or 'all'"))
    p.add_argument("percent", type=percent_arg, metavar="PERCENT")
    p.set_defaults(func=cmd_set)

    p = sub.add_parser("auto", help=_("hand a fan back to automatic control (or 'all')"))
    p.add_argument("fan")
    p.set_defaults(func=cmd_auto)

    p = sub.add_parser("rename", help=_("give a fan a name (no name: original name)"))
    p.add_argument("fan")
    p.add_argument("name", nargs="?")
    p.set_defaults(func=cmd_rename)

    p = sub.add_parser("hide", help=_("hide a fan (its setting does not change)"))
    p.add_argument("fan")
    p.set_defaults(func=cmd_hide)

    p = sub.add_parser("unhide", help=_("show a hidden fan again (or 'all')"))
    p.add_argument("fan")
    p.set_defaults(func=cmd_unhide)

    p = sub.add_parser("profile", help=_("manage profiles (saved sets of fan settings)"))
    p.add_argument("action", choices=("list", "save", "apply", "delete"), help=_("what to do with profiles"))
    p.add_argument("name", nargs="?", help=_("profile name (10 characters max)"))
    p.set_defaults(func=cmd_profile)

    p = sub.add_parser("detect", help=_("detailed hardware inventory, without the service"))
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_detect)

    p = sub.add_parser("gui", help=_("open the graphical interface"))
    p.set_defaults(func=cmd_gui)

    sub.add_parser("daemon", help=_("run the service (root; see \"fantastic daemon --help\")"))

    args = parser.parse_args(argv)
    if args.command == "profile" and args.action != "list" and not args.name:
        parser.error(_("a profile name is required"))
    if args.command is None:
        args = parser.parse_args(["list"])
    try:
        return args.func(args)
    except CliError as exc:
        print(_("Error: {error}", error=exc), file=sys.stderr)
    except DaemonError as exc:
        print(_("Refused by the service: {error}", error=exc), file=sys.stderr)
    except OSError as exc:
        print(_("fantasticd service unreachable ({error}). Is it running? sudo systemctl start fantasticd",
                error=exc), file=sys.stderr)
    return 1
