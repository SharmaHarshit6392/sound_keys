import random
import threading
from pathlib import Path

import keyboard
import pygame
import config


class SoundEngine:
    """Global keyboard sound engine for SoundKeys."""

    def __init__(self, on_status_change=None, on_exit=None):
        self.sound_dir = Path(__file__).parent / "sounds" / "chaos"
        self.max_channels = config.MAX_SIMULTANEOUS_SOUNDS
        self.mute_key = config.MUTE_KEY.lower()
        self.enter_key = "enter"
        self.enter_filename = config.ENTER_SOUND.lower()
        self.trigger_keys = {key.lower() for key in config.CHAOS_TRIGGER_KEYS}
        self.custom_assignments = {
            key.lower(): filename.lower()
            for key, filename in config.CUSTOM_KEY_SOUNDS.items()
        }

        self.mode = config.MODE.lower()
        self.running = False
        self.muted = False
        self._lock = threading.RLock()
        self._hook = None
        self._on_status_change = on_status_change
        self._on_exit = on_exit
        self._closed = False

        pygame.mixer.init()
        pygame.mixer.set_num_channels(self.max_channels)
        self.sounds = {}

        try:
            self._load_sounds()
        except Exception:
            pygame.mixer.quit()
            raise

    def _load_sounds(self):
        """Load MP3 files from the existing sound folder."""
        for file_path in self.sound_dir.glob("*.mp3"):
            try:
                self.sounds[file_path.name.lower()] = pygame.mixer.Sound(str(file_path))
            except pygame.error as error:
                print(f"Could not load {file_path.name}: {error}")

        if self.enter_filename not in self.sounds:
            raise FileNotFoundError(
                f"Missing Enter sound '{self.enter_filename}' in {self.sound_dir}"
            )

        if self.mode == "chaos":
            chaos_sounds = [
                name for name in self.sounds if name != self.enter_filename
            ]
            if not chaos_sounds:
                raise RuntimeError("Add at least one other MP3 to sounds/chaos.")

        if self.mode == "custom":
            for key, filename in self.custom_assignments.items():
                if filename not in self.sounds:
                    raise FileNotFoundError(
                        f"Sound '{filename}' assigned to '{key}' was not found in sounds/chaos."
                    )

    def start(self, mode=None):
        """Enable global keyboard sound detection."""
        with self._lock:
            if self._closed:
                raise RuntimeError("This SoundKeys engine has already been closed.")
            if self.running:
                return

            if mode is not None:
                normalized_mode = mode.lower().replace(" mode", "")
                if normalized_mode not in {"chaos", "custom"}:
                    raise ValueError(f"Unsupported mode: {mode}")
                self.mode = normalized_mode

            if self.mode == "custom":
                for key, filename in self.custom_assignments.items():
                    if filename not in self.sounds:
                        raise FileNotFoundError(
                            f"Missing sound '{filename}' assigned to '{key}'."
                        )
            elif self.mode == "chaos":
                if not any(name != self.enter_filename for name in self.sounds):
                    raise RuntimeError("No random Chaos Mode sounds are available.")

            self.running = True
            try:
                self._hook = keyboard.on_press(self._on_key_press)
            except Exception:
                self.running = False
                self._hook = None
                raise

        print(f"SoundKeys {self.mode.title()} Mode started.")
        if self._on_status_change:
            self._on_status_change(True)

    def stop(self):
        """Disable keyboard detection and stop playing sounds."""
        with self._lock:
            was_running = self.running
            self.running = False
            hook = self._hook
            self._hook = None
            pygame.mixer.stop()

        if hook is not None:
            try:
                keyboard.unhook(hook)
            except (KeyError, ValueError):
                pass

        if was_running:
            print("SoundKeys stopped.")
            if self._on_status_change:
                self._on_status_change(False)

    def toggle_mute(self):
        """Toggle actual audio playback mute."""
        with self._lock:
            self.muted = not self.muted
            if self.muted:
                pygame.mixer.stop()
            current_state = self.muted

        print("SoundKeys MUTED" if current_state else "SoundKeys UNMUTED")
        return current_state

    def _play(self, sound):
        """Play a sound if unmuted and a channel is available."""
        with self._lock:
            if not self.running or self.muted or self._closed:
                return
            channel = pygame.mixer.find_channel(False)
            if channel is not None:
                channel.play(sound)

    def _on_key_press(self, event):
        """Handle global keyboard events."""
        if event.event_type != "down":
            return

        key = event.name.lower()

        if key == self.mute_key:
            self.toggle_mute()
            return

        if key == "esc":
            self.stop()
            # Keep Tkinter calls out of the keyboard listener thread.
            # The GUI polls this callback through a thread-safe Event.
            if self._on_exit:
                try:
                    self._on_exit()
                except Exception as error:
                    print(f"Exit callback error: {error}")
            return

        if not self.running:
            return

        if key == self.enter_key:
            self._play(self.sounds[self.enter_filename])
            return

        if self.mode == "chaos":
            if key in self.trigger_keys:
                available_sounds = [
                    sound for filename, sound in self.sounds.items()
                    if filename != self.enter_filename
                ]
                if available_sounds:
                    self._play(random.choice(available_sounds))
        elif self.mode == "custom":
            filename = self.custom_assignments.get(key)
            if filename is not None:
                sound = self.sounds.get(filename)
                if sound is not None:
                    self._play(sound)

    def close(self):
        """Stop hooks and release audio resources; safe to call more than once."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self.stop()
        pygame.mixer.quit()
