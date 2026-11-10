# SoundKeys

**Your keyboard. Your sound.**

SoundKeys is a Windows desktop app that plays sound effects when you press keyboard keys. Choose a sound style, customize key assignments, and control playback from a compact desktop interface.

> **Release status:** SoundKeys v1.0.0 is published. Version v1.1.0 is currently under development and will be released after final Windows testing and packaging.

## Features

- **Chaos Mode** — trigger randomized sound effects with selected keys.
- **Custom Mode** — assign your own sound effects to supported keys.
- **Mechanical Mode** — choose among Blue, Red, Brown, and Black keyboard sound profiles.
- **Sound library** — import and preview your own audio files.
- **Global keyboard detection** — sound effects can be triggered while working in other desktop applications.
- **Quick controls** — start, stop, and mute playback.
- **System tray** — keep SoundKeys running in the background.
- **Backup and restore** — preserve your settings, mappings, and imported sounds.

## Download

Download the latest published version from the [GitHub Releases page](https://github.com/SharmaHarshit6392/sound_keys/releases).

1. Open the Releases page.
2. Download the Windows installer from the latest published release.
3. Run the installer and follow the prompts.
4. Launch SoundKeys from the Start menu or desktop shortcut.

Only download installers published under this repository's official Releases.

## Requirements

- Windows 10 or Windows 11, 64-bit.
- A working audio output device.
- The packaged installer is intended to include the runtime dependencies.

## Run from source

The v1.0.0 release is available under the `v1.0.0` Git tag.

The v1.1.0 development version includes Windows stability improvements, improved key mapping and preview behaviour, and backup restoration fixes.

Development setup instructions and the exact supported Python version will be documented before the v1.1.0 release.

## Audio files

SoundKeys supports importing personal sound effects into its sound library. Only use audio files that you created, have permission to use, or are otherwise properly licensed. Third-party sound files may have separate copyright and license terms; the MIT license for this project's code does not automatically apply to those audio files.

## Keyboard hook and privacy

SoundKeys listens for keyboard events so it can react to configured key presses. Use it only on devices and accounts where you are authorized to run keyboard-hooking software. SoundKeys is intended to process key presses for local sound playback, not to record or transmit typed text.

## Contributing

Bug reports and suggestions are welcome. Please open an issue with:
- Your Windows version.
- The SoundKeys version.
- Steps to reproduce the issue.
- Any relevant error message.

Please do not attach private data or unrelated audio files to issues.

## License

The application source code is licensed under the [MIT License](LICENSE).

