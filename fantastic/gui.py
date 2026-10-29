"""GTK 4 / libadwaita graphical interface.

The interface runs unprivileged: it reads the state and sends targets to the
fantasticd service. When the service is unreachable, it reads the hardware
directly and switches to read-only.

The language is chosen from the header bar (flag menu) and remembered in
~/.config/fantastic/settings.json; it defaults to the system language.
"""

from __future__ import annotations

import json
import os
import queue
import threading
import time

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Pango", "1.0")
from gi.repository import Adw, Gio, GLib, Gtk, Pango  # noqa: E402

from . import APP_ID, i18n  # noqa: E402
from .client import Client  # noqa: E402
from .fmt import fmt_percent, fmt_rpm, fmt_temp  # noqa: E402
from .hardware import Hardware  # noqa: E402
from .i18n import _, ngettext  # noqa: E402

POLL_MS = 1500
SEND_DELAY_MS = 120
# After a user action, values read back must not overwrite what the user just set.
USER_GRACE_S = 2.5
MAX_INLINE_TEMPS = 3

# Layout: device blocks are spread over 1, 2 or 3 columns depending on the width.
BREAKPOINTS = ((2, 900), (3, 1380))  # (columns, minimum window width in sp)
COLUMN_MAX_WIDTH = 640
SPACING = 24
MARGIN = 18
# Approximate heights (px) used to balance the columns.
GROUP_HEADER_H, FAN_ROW_H, READONLY_ROW_H, TEMP_ROW_H, TEMP_SUBTITLE_ROW_H = 70, 110, 62, 52, 58

SETTINGS_PATH = os.path.join(GLib.get_user_config_dir(), "fantastic", "settings.json")


def load_settings() -> dict:
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_settings(**changes) -> None:
    settings = {**load_settings(), **changes}
    try:
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except OSError:
        pass  # the preference is lost, nothing else


def escape(text: str | None) -> str:
    return GLib.markup_escape_text(text or "")


class Worker:
    """Runs service calls off the UI thread, in submission order."""

    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        threading.Thread(target=self._run, name="worker", daemon=True).start()

    def submit(self, fn, callback=None) -> None:
        self._queue.put((fn, callback))

    def _run(self) -> None:
        while True:
            fn, callback = self._queue.get()
            try:
                result, error = fn(), None
            except Exception as exc:
                result, error = None, exc
            if callback is not None:
                GLib.idle_add(callback, result, error)


class Backend:
    """Data source: the fantasticd service, or else a direct read-only access."""

    def __init__(self):
        self.client = Client(timeout=3)
        self.local: Hardware | None = None

    def status(self) -> dict:
        lang = i18n.get_language()
        try:
            data = self.client.call("status")
            data["source"] = "daemon"
        except OSError as exc:
            if self.local is None:
                self.local = Hardware()
            data = self.local.local_status(lang)
            data.update(source="local", daemon_error=str(exc))
        data["lang"] = lang
        return data

    def call(self, cmd: str, **params) -> dict:
        return self.client.call(cmd, **params)

    def rescan(self) -> None:
        try:
            self.client.call("rescan")
        except OSError:
            if self.local is not None:
                self.local.scan()


class FanRow(Adw.PreferencesRow):
    """A fan: name, measured speed, "Auto" switch and 0-100% slider."""

    def __init__(self, window: MainWindow, fan: dict):
        super().__init__(activatable=False)
        self.window = window
        self.fan_id = fan["id"]
        self.controllable = fan["controllable"]
        self.min_percent = fan.get("min_percent") or 0
        self.name = fan["name"]
        self._updating = False
        self._touched = 0.0

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6,
                      margin_top=10, margin_bottom=10, margin_start=12, margin_end=12)
        header = Gtk.Box(spacing=12)
        texts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, valign=Gtk.Align.CENTER)
        self.title = Gtk.Label(xalign=0, ellipsize=Pango.EllipsizeMode.END)
        self.subtitle = Gtk.Label(xalign=0, ellipsize=Pango.EllipsizeMode.END)
        self.subtitle.add_css_class("dim-label")
        self.subtitle.add_css_class("caption")
        texts.append(self.title)
        texts.append(self.subtitle)
        header.append(texts)
        self.rename_button = self._make_rename_button()
        header.append(self.rename_button)
        self.hide_button = Gtk.Button(icon_name="view-conceal-symbolic", valign=Gtk.Align.CENTER,
                                      tooltip_text=_("Hide this fan"))
        self.hide_button.add_css_class("flat")
        self.hide_button.connect("clicked", lambda *_args: self.window.send_hide(self.fan_id, self.name))
        header.append(self.hide_button)
        box.append(header)

        if self.controllable:
            auto = Gtk.Box(spacing=6, valign=Gtk.Align.CENTER)
            auto_label = Gtk.Label(label=_("Auto"))
            auto_label.add_css_class("dim-label")
            self.switch = Gtk.Switch(valign=Gtk.Align.CENTER, tooltip_text=_("Let the hardware set the speed"))
            self.switch.connect("notify::active", self._on_switch)
            auto.append(auto_label)
            auto.append(self.switch)
            header.append(auto)

            slider = Gtk.Box(spacing=12)
            self.scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
            self.scale.set_hexpand(True)
            self.scale.set_draw_value(False)
            self.scale.set_round_digits(0)
            for mark in (0, 25, 50, 75, 100):
                self.scale.add_mark(mark, Gtk.PositionType.BOTTOM, None)
            if self.min_percent:
                self.scale.add_mark(self.min_percent, Gtk.PositionType.BOTTOM,
                                    _("min. {value}", value=fmt_percent(self.min_percent)))
            self.scale.connect("value-changed", self._on_scale)
            self.value_label = Gtk.Label(width_chars=6, xalign=1)
            self.value_label.add_css_class("numeric")
            slider.append(self.scale)
            slider.append(self.value_label)
            box.append(slider)

        self.set_child(box)

    def _make_rename_button(self) -> Gtk.MenuButton:
        entry = Gtk.Entry(placeholder_text=_("Empty = original name"), width_chars=24)
        ok = Gtk.Button(label=_("Rename"))
        ok.add_css_class("suggested-action")
        box = Gtk.Box(spacing=6, margin_top=6, margin_bottom=6, margin_start=6, margin_end=6)
        box.append(entry)
        box.append(ok)
        popover = Gtk.Popover(child=box)

        def submit(*_args):
            self.window.send_rename(self.fan_id, entry.get_text().strip())
            popover.popdown()

        def on_show(*_args):
            entry.set_text(self.name)
            entry.grab_focus()

        entry.connect("activate", submit)
        ok.connect("clicked", submit)
        popover.connect("show", on_show)
        button = Gtk.MenuButton(icon_name="document-edit-symbolic", valign=Gtk.Align.CENTER,
                                tooltip_text=_("Rename this fan"), popover=popover)
        button.add_css_class("flat")
        return button

    def update(self, fan: dict, controls: bool, failsafe: bool) -> None:
        self.name = fan["name"]
        self.title.set_text(self.name)
        self.subtitle.set_text(self._subtitle(fan, failsafe))
        self.rename_button.set_sensitive(controls)
        self.hide_button.set_sensitive(controls)
        if not self.controllable:
            return
        self.scale.set_sensitive(controls)
        self.switch.set_sensitive(controls)
        if time.monotonic() - self._touched < USER_GRACE_S:
            return
        target = fan.get("target")
        value = target if target is not None else fan.get("percent")
        self._updating = True
        try:
            self.switch.set_active(target is None and fan.get("mode") != "manual")
            if value is not None:
                self.scale.set_value(value)
            self.value_label.set_text(fmt_percent(value))
        finally:
            self._updating = False

    def _subtitle(self, fan: dict, failsafe: bool) -> str:
        parts = [fmt_rpm(fan.get("rpm"))]
        if not self.controllable:
            parts.append(_("read-only"))
        elif fan.get("target") is not None:
            parts.append(_("thermal failsafe: 100%") if failsafe else _("manual"))
        else:
            parts.append(_("manual") if fan.get("mode") == "manual" else _("automatic"))
        if self.name != fan["label"]:
            parts.append(fan["label"])
        parts.append(fan["channel"])
        if fan.get("error"):
            parts.append(f"⚠ {fan['error']}")
        return " · ".join(parts)

    def _on_scale(self, scale: Gtk.Scale) -> None:
        if self._updating:
            return
        value = int(round(scale.get_value()))
        self._updating = True
        try:
            if value < self.min_percent:
                value = self.min_percent
                scale.set_value(value)
            self.switch.set_active(False)
        finally:
            self._updating = False
        self._touched = time.monotonic()
        self.value_label.set_text(fmt_percent(value))
        self.window.queue_set(self.fan_id, value)

    def _on_switch(self, switch: Gtk.Switch, _pspec) -> None:
        if self._updating:
            return
        self._touched = time.monotonic()
        if switch.get_active():
            self.window.send_auto(self.fan_id)
        else:
            self.window.queue_set(self.fan_id, max(self.min_percent, int(round(self.scale.get_value()))))


class TempRow(Adw.ActionRow):
    def __init__(self, temp: dict, subtitle: str = ""):
        super().__init__(title=temp["label"], subtitle=subtitle, use_markup=False)
        self.value = Gtk.Label()
        self.value.add_css_class("numeric")
        self.add_suffix(self.value)
        self.update(temp)

    def update(self, temp: dict) -> None:
        self.value.set_text(fmt_temp(temp["celsius"]))


class HintRow(Adw.ActionRow):
    def __init__(self, window: MainWindow, hint: dict):
        super().__init__(title=hint["text"], use_markup=False)
        self.add_prefix(Gtk.Image(icon_name="dialog-information-symbolic"))
        command = hint.get("command")
        if command:
            self.set_subtitle(command)
            self.set_subtitle_selectable(True)
            button = Gtk.Button(icon_name="edit-copy-symbolic", valign=Gtk.Align.CENTER,
                                tooltip_text=_("Copy the command"))
            button.add_css_class("flat")
            button.connect("clicked", lambda *_args: window.copy(command))
            self.add_suffix(button)


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application):
        super().__init__(application=app, title="Fantastic", default_width=1120, default_height=780,
                         width_request=400, height_request=480)
        self.backend = Backend()
        self.worker = Worker()
        self.fan_rows: dict[str, FanRow] = {}
        self.temp_rows: dict[str, TempRow] = {}
        self.groups: list[Adw.PreferencesGroup] = []
        self.device_groups: list[tuple[Adw.PreferencesGroup, int]] = []
        self.n_columns = 1
        self.hidden_count = 0
        self._relayout_source = 0
        self._signature = None
        self._pending: dict[str, int] = {}
        self._flush_source = 0
        self._polling = False

        self.window_title = Adw.WindowTitle(title="Fantastic")
        header = Adw.HeaderBar(title_widget=self.window_title)
        self.rescan_button = Gtk.Button(icon_name="view-refresh-symbolic")
        self.rescan_button.connect("clicked", self._on_rescan)
        header.pack_start(self.rescan_button)
        self.reveal_content = Adw.ButtonContent(icon_name="view-reveal-symbolic", label="0")
        self.reveal_button = Gtk.Button(child=self.reveal_content, visible=False)
        self.reveal_button.connect("clicked", self._confirm_unhide_all)
        header.pack_start(self.reveal_button)

        self.language_button = Gtk.MenuButton(menu_model=self._language_menu())
        header.pack_end(self.language_button)
        language = Gio.SimpleAction.new_stateful(
            "language", GLib.VariantType.new("s"), GLib.Variant.new_string(i18n.get_language()))
        language.connect("change-state", self._on_language)
        self.add_action(language)

        self.presets = Gtk.Box(sensitive=False)
        self.presets.add_css_class("linked")
        self.preset_buttons = []
        for percent in (None, 20, 100):  # None: everything back to automatic
            button = Gtk.Button()
            button.connect("clicked", lambda _button, p=percent: self.send_auto_all() if p is None
                           else self.send_all(p))
            self.presets.append(button)
            self.preset_buttons.append((button, percent))
        header.pack_end(self.presets)

        self.banner = Adw.Banner()
        # Hints and messages span the full width, devices go into columns below.
        self.top_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=SPACING)
        self.columns = Gtk.Box(spacing=SPACING, homogeneous=True)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=SPACING,
                          margin_top=SPACING, margin_bottom=SPACING, margin_start=MARGIN, margin_end=MARGIN)
        content.append(self.top_box)
        content.append(self.columns)
        self.clamp = Adw.Clamp(child=content, maximum_size=COLUMN_MAX_WIDTH)
        self.scroller = Gtk.ScrolledWindow(child=self.clamp, vexpand=True,
                                           hscrollbar_policy=Gtk.PolicyType.NEVER)
        self.toasts = Adw.ToastOverlay(child=self.scroller)
        view = Adw.ToolbarView(content=self.toasts)
        view.add_top_bar(header)
        view.add_top_bar(self.banner)
        self.set_content(view)

        self._breakpoint_columns = {}
        for columns, min_width in BREAKPOINTS:
            breakpoint = Adw.Breakpoint.new(Adw.BreakpointCondition.parse(f"min-width: {min_width}sp"))
            self.add_breakpoint(breakpoint)
            self._breakpoint_columns[breakpoint] = columns
        self.connect("notify::current-breakpoint", self._on_breakpoint)

        self._apply_texts()
        self.window_title.set_subtitle(_("Detecting…"))
        self._poll()
        GLib.timeout_add(POLL_MS, self._poll)

    # --- language ----------------------------------------------------------

    @staticmethod
    def _language_menu() -> Gio.Menu:
        menu = Gio.Menu()
        for code, (name, flag) in i18n.LANGUAGES.items():
            menu.append(f"{flag}  {name}", f"win.language::{code}")
        return menu

    def _on_language(self, action: Gio.SimpleAction, value: GLib.Variant) -> None:
        action.set_state(value)
        i18n.set_language(value.get_string())
        save_settings(language=i18n.get_language())
        self._apply_texts()
        self._signature = None  # rebuild every row with the new language
        self._poll()

    def _apply_texts(self) -> None:
        """Texts of the widgets that live as long as the window."""
        name, flag = i18n.LANGUAGES[i18n.get_language()]
        self.language_button.set_label(flag)
        self.language_button.set_tooltip_text(_("Language: {name}", name=name))
        self.rescan_button.set_tooltip_text(_("Look for new fans"))
        self.reveal_button.set_tooltip_text(_("Show hidden fans again"))
        for button, percent in self.preset_buttons:
            if percent is None:
                button.set_label(_("Auto"))
                button.set_tooltip_text(_("Hand every fan, hidden ones included, back to automatic control"))
            else:
                button.set_label(fmt_percent(percent))
                button.set_tooltip_text(_("Every visible fan at {value} (or at its minimum)",
                                          value=fmt_percent(percent)))

    # --- service calls -----------------------------------------------------

    def _poll(self) -> bool:
        if not self._polling:
            self._polling = True
            self.worker.submit(self.backend.status, self._on_status)
        return GLib.SOURCE_CONTINUE

    def queue_set(self, fan_id: str, percent: int) -> None:
        # While the slider is being dragged, only the latest value is sent.
        self._pending[fan_id] = percent
        if not self._flush_source:
            self._flush_source = GLib.timeout_add(SEND_DELAY_MS, self._flush)

    def _flush(self) -> bool:
        self._flush_source = 0
        pending, self._pending = self._pending, {}
        for fan_id, percent in pending.items():
            self.worker.submit(lambda f=fan_id, p=percent: self.backend.call("set", fan=f, percent=p),
                               self._on_command_done)
        return GLib.SOURCE_REMOVE

    def send_auto(self, fan_id: str) -> None:
        self._pending.pop(fan_id, None)
        self.worker.submit(lambda: self.backend.call("auto", fan=fan_id), self._on_command_done)

    def send_all(self, percent: int) -> None:
        self._pending.clear()

        def done(result, error):
            if error is None:
                count = len(result["applied"])
                text = ngettext("{n} fan at {value}", "{n} fans at {value}", count, value=fmt_percent(percent))
                if any(value != percent for value in result["applied"].values()):
                    text += " " + _("(hardware minimum applied for some)")
                self.toast(text)
            self._on_bulk_done(result, error)

        self.worker.submit(lambda: self.backend.call("set_all", percent=percent), done)

    def send_auto_all(self) -> None:
        self._pending.clear()
        self.worker.submit(lambda: self.backend.call("auto_all"), self._on_bulk_done)

    def _on_bulk_done(self, result, error) -> None:
        if error is None and result["errors"]:
            first = next(iter(result["errors"].values()))
            error = ngettext("{n} fan failed: {error}", "{n} fans failed: {error}", len(result["errors"]),
                             error=first)
        self._on_command_done(result, error)

    def send_rename(self, fan_id: str, name: str) -> None:
        self.worker.submit(lambda: self.backend.call("rename", fan=fan_id, name=name), self._on_command_done)

    def send_hide(self, fan_id: str, name: str) -> None:
        def set_hidden(hidden: bool):
            return lambda: self.backend.call("hide", fan=fan_id, hidden=hidden)

        def done(_result, error):
            if error is None:
                # No confirmation to hide: the toast offers to undo instead.
                toast = Adw.Toast(title=escape(_("'{name}' hidden", name=name)), button_label=_("Undo"),
                                  timeout=5)
                toast.connect("button-clicked",
                              lambda *_args: self.worker.submit(set_hidden(False), self._on_command_done))
                self.toasts.add_toast(toast)
            self._on_command_done(None, error)

        self.worker.submit(set_hidden(True), done)

    def _confirm_unhide_all(self, _button) -> None:
        body = ngettext("{n} hidden fan will reappear in the window. Its setting does not change.",
                        "{n} hidden fans will reappear in the window. Their settings do not change.",
                        self.hidden_count)
        dialog = Adw.AlertDialog(heading=_("Show hidden fans again?"), body=body)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("show", _("Show"))
        dialog.set_response_appearance("show", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("show")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_unhide_response)
        dialog.present(self)

    def _on_unhide_response(self, _dialog, response: str) -> None:
        if response == "show":
            self.worker.submit(lambda: self.backend.call("unhide_all"), self._on_command_done)

    def _on_rescan(self, _button) -> None:
        self.worker.submit(self.backend.rescan, self._on_command_done)

    def _on_command_done(self, _result, error) -> None:
        if error is not None:
            self.toast(_("Error: {error}", error=error))
        self._poll()

    def toast(self, text: str) -> None:
        self.toasts.add_toast(Adw.Toast(title=escape(text), timeout=5))

    def copy(self, text: str) -> None:
        self.get_clipboard().set(text)
        self.toast(_("Command copied"))

    # --- display -----------------------------------------------------------

    def _on_status(self, data: dict | None, error: Exception | None) -> None:
        self._polling = False
        if error is not None:
            self._show_banner(_("Read error: {error}", error=error))
            return
        controls = data["source"] == "daemon" and data.get("authorized", False)
        failsafe = data.get("failsafe", False)
        self.presets.set_sensitive(controls)
        if data["source"] != "daemon":
            self._show_banner(_("fantasticd service unreachable: read-only display. "
                                "Start it with \"sudo systemctl start fantasticd\"."))
        elif not data.get("authorized"):
            self._show_banner(_("Your account is not allowed to control fans: "
                                "see allowed_users in /etc/fantastic/config.json."))
        elif failsafe:
            self._show_banner(_("Thermal failsafe: a temperature exceeds {temp} °C, "
                                "manually set fans run at 100%.", temp=data.get("failsafe_temp")))
        else:
            self.banner.set_revealed(False)

        fans = [f for f in data["fans"] if not f.get("hidden")]
        self.hidden_count = len(data["fans"]) - len(fans)
        data = {**data, "fans": fans}
        controllable = sum(1 for f in fans if f["controllable"])
        subtitle = ngettext("{n} fan", "{n} fans", len(fans)) + " · " + \
            ngettext("{n} controllable", "{n} controllable", controllable)
        if self.hidden_count:
            subtitle += " · " + ngettext("{n} hidden", "{n} hidden", self.hidden_count)
        self.window_title.set_subtitle(subtitle)
        self.reveal_content.set_label(str(self.hidden_count))
        self.reveal_button.set_visible(self.hidden_count > 0)
        self.reveal_button.set_sensitive(controls)

        signature = (data.get("lang"), self.hidden_count > 0,
                     tuple(d["id"] for d in data["devices"]),
                     tuple(f["id"] for f in fans),
                     tuple(t["id"] for t in data["temps"]),
                     tuple(h["text"] for h in data.get("hints", [])))
        if signature != self._signature:
            self._signature = signature
            self._rebuild(data)
        for fan in fans:
            self.fan_rows[fan["id"]].update(fan, controls, failsafe)
        for temp in data["temps"]:
            self.temp_rows[temp["id"]].update(temp)

    def _show_banner(self, text: str) -> None:
        self.banner.set_title(escape(text))
        self.banner.set_revealed(True)

    def _add_group(self, group: Adw.PreferencesGroup, weight: int | None = None) -> None:
        """Adds a block: full width (weight=None) or into the device columns."""
        self.groups.append(group)
        if weight is None:
            self.top_box.append(group)
        else:
            self.device_groups.append((group, weight))

    def _on_breakpoint(self, *_args) -> None:
        columns = self._breakpoint_columns.get(self.get_current_breakpoint(), 1)
        if columns != self.n_columns:
            self.n_columns = columns
            # Outside the current allocation phase: rearrange on the next main loop iteration.
            if not self._relayout_source:
                self._relayout_source = GLib.idle_add(self._layout)

    def _layout(self) -> bool:
        """Spreads device blocks over the columns, each into the shortest column."""
        self._relayout_source = 0
        for group, _weight in self.device_groups:
            if (parent := group.get_parent()) is not None:
                parent.remove(group)
        while (column := self.columns.get_first_child()) is not None:
            self.columns.remove(column)
        n = self.n_columns
        columns = [Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=SPACING) for _index in range(n)]
        heights = [0] * n
        for group, weight in self.device_groups:
            shortest = heights.index(min(heights))
            columns[shortest].append(group)
            heights[shortest] += weight
        for column in columns:
            self.columns.append(column)
        self.clamp.set_maximum_size(n * COLUMN_MAX_WIDTH + (n - 1) * SPACING)
        return GLib.SOURCE_REMOVE

    def _rebuild(self, data: dict) -> None:
        for group in self.groups:
            if (parent := group.get_parent()) is not None:
                parent.remove(group)
        self.groups.clear()
        self.device_groups.clear()
        self.fan_rows.clear()
        self.temp_rows.clear()

        fans_by_device: dict[str, list] = {}
        temps_by_device: dict[str, list] = {}
        for fan in data["fans"]:
            fans_by_device.setdefault(fan["device_id"], []).append(fan)
        for temp in data["temps"]:
            temps_by_device.setdefault(temp["device_id"], []).append(temp)

        if data.get("hints"):
            group = Adw.PreferencesGroup(title=escape(_("Suggestions")))
            for hint in data["hints"]:
                group.add(HintRow(self, hint))
            self._add_group(group)

        if not data["fans"]:
            group = Adw.PreferencesGroup()
            if self.hidden_count:
                row = Adw.ActionRow(title=_("All fans are hidden"),
                                    subtitle=_("The eye-shaped button, top left, shows them again."),
                                    use_markup=False)
            else:
                row = Adw.ActionRow(title=_("No fan detected"),
                                    subtitle=_("See the suggestions and the README."), use_markup=False)
            group.add(row)
            self._add_group(group)

        for device in data["devices"]:
            if device["id"] not in fans_by_device:
                continue
            group = Adw.PreferencesGroup(title=escape(device["name"]), description=escape(device["details"]))
            weight = GROUP_HEADER_H
            for fan in fans_by_device[device["id"]]:
                row = FanRow(self, fan)
                self.fan_rows[fan["id"]] = row
                group.add(row)
                weight += FAN_ROW_H if fan["controllable"] else READONLY_ROW_H
            temps = temps_by_device.get(device["id"], [])
            # Motherboards often expose a dozen probes: fold them.
            container = group
            if len(temps) > MAX_INLINE_TEMPS:
                container = Adw.ExpanderRow(title=_("Temperatures ({n})", n=len(temps)), use_markup=False)
                group.add(container)
                weight += TEMP_ROW_H
            else:
                weight += TEMP_ROW_H * len(temps)
            for temp in temps:
                row = TempRow(temp)
                self.temp_rows[temp["id"]] = row
                if container is group:
                    group.add(row)
                else:
                    container.add_row(row)
            self._add_group(group, weight)

        others = [d for d in data["devices"] if d["id"] not in fans_by_device and d["id"] in temps_by_device]
        if others:
            group = Adw.PreferencesGroup(title=escape(_("Other temperatures")))
            weight = GROUP_HEADER_H
            for device in others:
                for temp in temps_by_device[device["id"]]:
                    row = TempRow(temp, subtitle=device["name"])
                    self.temp_rows[temp["id"]] = row
                    group.add(row)
                    weight += TEMP_SUBTITLE_ROW_H
            self._add_group(group, weight)

        self._layout()


class FantasticApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_args: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<Control>q"])

    def do_activate(self) -> None:
        window = self.get_active_window() or MainWindow(self)
        window.present()


def main() -> int:
    i18n.set_language(load_settings().get("language") or i18n.system_language())
    Gtk.Window.set_default_icon_name(APP_ID)
    return FantasticApp().run(None)
