#!/usr/bin/python
import os
import subprocess
import sys

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, GLib, Gtk

SOURCE = "alsa_input.pci-0000_00_1f.3.analog-stereo"
INTERNAL = "analog-input-internal-mic"
HEADSET = "analog-input-headset-mic"

HUNGARIAN = {
    "Audio Jack": "Jack csatlakozó",
    "What did you plug in?": "Mit csatlakoztattál?",
    "Headphones": "Fejhallgató",
    "Headset (with microphone)": "Headset (mikrofonnal)",
    "Could not switch the microphone input.": "A mikrofonbemenet váltása sikertelen.",
}


def jack_connected():
    result = subprocess.run(
        ["amixer", "-c", "PCH", "cget", "iface=CARD,name=Headphone Mic Jack"],
        capture_output=True, text=True, env={**os.environ, "LC_ALL": "C"},
    )
    if result.returncode:
        return None
    return ": values=on" in result.stdout


class JackPicker(Gtk.Application):
    def __init__(self, preview):
        super().__init__(
            application_id="local.omarchy.JackPicker",
            flags=Gio.ApplicationFlags.NON_UNIQUE,
        )
        language = next(
            (name for name in GLib.get_language_names() if name in ("en", "hu")),
            "en",
        )
        self.labels = HUNGARIAN if language == "hu" else {}
        self.preview = preview
        self.connected = None
        self.window = None
        self.using_headset = False

    def translate(self, message):
        return self.labels.get(message, message)

    def do_activate(self):
        if self.preview:
            self.show_picker()
            return
        self.hold()
        self.connected = jack_connected()
        GLib.timeout_add_seconds(1, self.check_jack)

    def check_jack(self):
        connected = jack_connected()
        if connected is None or connected == self.connected:
            return GLib.SOURCE_CONTINUE
        previous, self.connected = self.connected, connected
        if connected and previous is False:
            self.show_picker()
        elif not connected:
            if self.window:
                self.window.close()
            if self.using_headset:
                self.set_port(INTERNAL)
        return GLib.SOURCE_CONTINUE

    def set_port(self, port):
        result = subprocess.run(
            ["pactl", "set-source-port", SOURCE, port],
            capture_output=True, text=True,
        )
        if result.returncode:
            print(result.stderr.strip(), file=sys.stderr, flush=True)
            return False
        self.using_headset = port == HEADSET
        return True

    def choose(self, port):
        if self.set_port(port):
            self.window.close()
        else:
            self.status.set_text(self.translate("Could not switch the microphone input."))

    def show_picker(self):
        if self.window:
            self.window.present()
            return
        window = Gtk.ApplicationWindow(
            application=self, title=self.translate("Audio Jack"), resizable=False,
        )
        self.window = window
        window.connect("close-request", self.on_close)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        for edge in ("top", "bottom", "start", "end"):
            getattr(content, "set_margin_" + edge)(20)
        window.set_child(content)
        content.append(Gtk.Label(label=self.translate("What did you plug in?")))
        buttons = Gtk.Box(spacing=10, homogeneous=True)
        content.append(buttons)
        for message, port, icon in (
            ("Headphones", INTERNAL, "audio-headphones-symbolic"),
            ("Headset (with microphone)", HEADSET, "audio-headset-symbolic"),
        ):
            label = self.translate(message)
            button = Gtk.Button()
            button.update_property([Gtk.AccessibleProperty.LABEL], [label])
            button_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            button_content.set_margin_top(10)
            button_content.set_margin_bottom(10)
            image = Gtk.Image.new_from_icon_name(icon)
            image.set_pixel_size(40)
            button_content.append(image)
            button_content.append(Gtk.Label(label=label))
            button.set_child(button_content)
            button.connect("clicked", lambda _, choice=port: self.choose(choice))
            buttons.append(button)
        self.status = Gtk.Label()
        content.append(self.status)
        window.present()

    def on_close(self, _window):
        self.window = None
        return False


if __name__ == "__main__":
    raise SystemExit(JackPicker("--preview" in sys.argv).run([sys.argv[0]]))
