"""Generates docs/screenshot.png: off-screen rendering of the interface (header bar + full content).

Usage (from the repository root, with the service running so that sliders are active):
    python3 tools/screenshot.py [--out docs/screenshot.png] [--lang en] [--width 1400] [--max-height 0]

The width selects the layout: 3 columns from 1380 px, 2 from 900.

The interface is only displayed: no fan speed is changed.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Graphene", "1.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Adw, GdkPixbuf, Gio, GLib, Graphene, Gtk  # noqa: E402

from fantastic import gui, i18n  # noqa: E402


def find(widget: Gtk.Widget, cls: type) -> Gtk.Widget | None:
    child = widget.get_first_child()
    while child is not None:
        if isinstance(child, cls):
            return child
        if (found := find(child, cls)) is not None:
            return found
        child = child.get_next_sibling()
    return None


def render(win: gui.MainWindow, path: str, max_height: int) -> None:
    header = find(win, Adw.HeaderBar)
    content = find(win.scroller, Gtk.Viewport).get_child()
    width, header_h, content_h = win.get_width(), header.get_height(), content.get_height()
    height = header_h + content_h
    _, background = win.get_style_context().lookup_color("window_bg_color")

    snapshot = Gtk.Snapshot()
    snapshot.append_color(background, Graphene.Rect().init(0, 0, width, height))
    Gtk.WidgetPaintable.new(header).snapshot(snapshot, width, header_h)
    snapshot.translate(Graphene.Point().init(0, header_h))
    Gtk.WidgetPaintable.new(content).snapshot(snapshot, content.get_width(), content_h)
    texture = win.get_native().get_renderer().render_texture(
        snapshot.to_node(), Graphene.Rect().init(0, 0, width, height))
    texture.save_to_png(path)

    if max_height and height > max_height:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
        pixbuf.new_subpixbuf(0, 0, width, max_height).savev(path, "png", [], [])
        height = max_height
    print(f"{path}: {width} x {height}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default="docs/screenshot.png")
    parser.add_argument("--lang", default="en", choices=sorted(i18n.LANGUAGES))
    parser.add_argument("--width", type=int, default=1400)
    parser.add_argument("--max-height", type=int, default=0, help="crop height (0 = full page)")
    parser.add_argument("--delay", type=int, default=4000, help="time to wait for data, in ms")
    args = parser.parse_args()
    i18n.set_language(args.lang)

    original_init = gui.MainWindow.__init__

    def init(self, app):
        original_init(self, app)
        self.set_default_size(args.width, 800)

    gui.MainWindow.__init__ = init
    app = gui.FantasticApp()
    # Separate instance, even if Fantastic is already open on the desktop.
    app.set_flags(app.get_flags() | Gio.ApplicationFlags.NON_UNIQUE)

    def shoot():
        render(app.get_active_window(), args.out, args.max_height)
        app.quit()
        return GLib.SOURCE_REMOVE

    GLib.timeout_add(args.delay, shoot)
    return app.run(None)


if __name__ == "__main__":
    sys.exit(main())
