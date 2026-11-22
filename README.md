# Omarchy Jack Picker

An Ubuntu-style chooser for wired 3.5 mm combo jacks on Omarchy. When it detects a plug insertion, it asks what you connected.

| Choice | Microphone input |
| --- | --- |
| **Headphones** | Laptop's built-in microphone |
| **Headset (with microphone)** | Microphone on the 3.5 mm jack |

The dialog follows the session's language preferences. It includes English and Hungarian, with English as the fallback. The chooser changes the microphone input port. Headphone playback is managed by the desktop audio stack.

## Requirements

You need an Omarchy graphical session with a systemd user manager, Python with PyGObject and GTK 4, ALSA's `amixer`, and `pactl` with a running PipeWire PulseAudio server.

## Check compatibility

This prototype uses the ALSA control and PipeWire source names from a Dell laptop with a Realtek ALC289 codec. It needs a readable jack state that changes on unplug and replug, plus selectable internal and headset microphone ports.

Run these in your graphical session:

```sh
amixer -c PCH cget 'iface=CARD,name=Headphone Mic Jack'
pactl list sources
```

Look for `values=off` with the plug out and `values=on` with it in. The source should list both `analog-input-internal-mic` and `analog-input-headset-mic`. On other hardware, use `amixer -l`, `amixer -c CARD controls`, and `pactl list sources` to find the corresponding names, then update the `amixer` arguments and source/port constants in `jack-picker.py` before installing.

## Install

From the repository root, with no existing jack-picker installation:

```sh
install -Dm644 jack-picker.py ~/.config/omarchy/jack-picker.py
install -Dm644 omarchy-jack-picker.service ~/.config/systemd/user/omarchy-jack-picker.service
systemctl --user daemon-reload
systemctl --user enable --now omarchy-jack-picker.service
```

The service starts with the graphical session. If the plug is already inserted when the service starts, unplug it, wait two seconds, and plug it back in. Choose **Headset (with microphone)** and speak into it while checking the input meter in Omarchy's audio panel.

To open the dialog manually from the repository root:

```sh
python jack-picker.py --preview
```

Both preview buttons apply their corresponding microphone setting. Close the window to dismiss it.

## Troubleshooting

Check the service and its logs if the dialog does not appear:

```sh
systemctl --user status omarchy-jack-picker.service
journalctl --user -u omarchy-jack-picker.service -b
```

## Uninstall

```sh
systemctl --user disable --now omarchy-jack-picker.service
rm ~/.config/systemd/user/omarchy-jack-picker.service ~/.config/omarchy/jack-picker.py
systemctl --user daemon-reload
```
