import json
import os
import random
import threading
from pathlib import Path

import keyboard
import pygame
from pygame import event
import config


class SoundEngine:
    """Global keyboard sound engine for SoundKeys."""

    SUPPORTED = {".mp3", ".wav", ".ogg", ".flac"}
    MECHANICAL_SPECIAL_KEYS = {
        "space": "space",
        "enter": "enter",
        "backspace": "backspace",
        "shift": "shift",
        "left shift": "shift",
        "right shift": "shift",
        "tab": "tab",
        "caps lock": "caps_lock",
    }

    def __init__(self, on_status_change=None, on_exit=None):
        # Bundled, read-only assets live beside this module (also works in PyInstaller).
        self.root = Path(__file__).resolve().parent
        self.chaos_dir = self.root / "sounds" / "chaos"
        self.mechanical_dir = self.root / "sounds" / "mechanical"

        # User-editable data must live outside Program Files.
        local_app_data = Path(
            os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
        )
        self.user_data_dir = local_app_data / "SoundKeys"
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self.custom_dir = self.user_data_dir / "sounds" / "custom"
        self.custom_dir.mkdir(parents=True, exist_ok=True)
        self.mapping_file = self.user_data_dir / "key_mappings.json"
        legacy_mapping = self.root / "key_mappings.json"
        if not self.mapping_file.exists() and legacy_mapping.is_file():
            import shutil
            shutil.copy2(legacy_mapping, self.mapping_file)

        self.max_channels = config.MAX_SIMULTANEOUS_SOUNDS
        self.mute_key = config.MUTE_KEY.lower()
        self.enter_key = "enter"
        self.enter_filename = config.ENTER_SOUND.lower()
        self.trigger_keys = {key.lower() for key in config.CHAOS_TRIGGER_KEYS}
        self.mechanical_profile = getattr(config, "MECHANICAL_PROFILE", "blue").lower()
        # Mechanical mode shares the same universal volume as every other mode.
        self.mechanical_volume = 1.0
        self.master_volume = max(0.0, min(1.0, float(getattr(config, "MASTER_VOLUME", 0.80))))

        self.custom_assignments = {}
        self._load_mappings()
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
        self.mechanical_sounds = {}
        self._profile_debug_pending = False
        try:
            self._load_sounds()
        except Exception:
            pygame.mixer.quit()
            raise

    def _load_mappings(self):
        if not self.mapping_file.exists():
            self.custom_assignments = {
                key.lower(): filename.lower()
                for key, filename in config.CUSTOM_KEY_SOUNDS.items()
            }
            return
        try:
            data = json.loads(self.mapping_file.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Invalid key mappings format.")
            self.custom_assignments = {
                key.lower(): filename
                for key, filename in data.items()
                if isinstance(key, str)
                and isinstance(filename, str)
                and Path(filename).name == filename
            }
        except (OSError, json.JSONDecodeError, ValueError) as error:
            print(f"Could not load key mappings: {error}")
            self.custom_assignments = {
                key.lower(): filename.lower()
                for key, filename in config.CUSTOM_KEY_SOUNDS.items()
            }

    def _load_sounds(self):
        self.sounds.clear()
        for folder in (self.chaos_dir, self.custom_dir):
            if not folder.exists():
                continue
            for path in folder.iterdir():
                if not path.is_file() or path.suffix.lower() not in self.SUPPORTED:
                    continue
                try:
                    # Custom files take precedence if filenames collide.
                    sound = pygame.mixer.Sound(str(path))
                    sound.set_volume(self.master_volume)
                    self.sounds[path.name.lower()] = sound
                except pygame.error as error:
                    print(f"Could not load {path.name}: {error}")

        if self.mode == "chaos" and self.enter_filename not in self.sounds:
            raise FileNotFoundError(
                f"Missing Chaos Mode Enter sound '{self.enter_filename}'. "
                "Check sounds/chaos."
            )

    def _build_mechanical_sounds(self, profile):
        """Build and validate a profile's sounds without disturbing the active pack."""
        profile_dir = self.mechanical_dir / profile
        if not profile_dir.exists():
            raise FileNotFoundError(
                f"Mechanical profile folder not found: {profile_dir}\n"
                "Create it and add key.wav (plus optional special-key sounds)."
            )

        loaded_sounds = {}
        for path in profile_dir.iterdir():
            if not path.is_file() or path.suffix.lower() not in self.SUPPORTED:
                continue
            try:
                sound = pygame.mixer.Sound(str(path))
                sound.set_volume(self.mechanical_volume * self.master_volume)
                loaded_sounds[path.stem.lower()] = sound
            except pygame.error as error:
                print(f"Could not load mechanical sound {path.name}: {error}")

        if not loaded_sounds:
            raise RuntimeError(
                f"No supported audio files found in {profile_dir}. "
                "Add at least key.wav."
            )
        return loaded_sounds

    def set_master_volume(self, value):
        """Apply the global volume multiplier to all loaded sound objects."""
        self.master_volume = max(0.0, min(1.0, float(value)))
        with self._lock:
            for sound in self.sounds.values():
                sound.set_volume(self.master_volume)
            for sound in self.mechanical_sounds.values():
                sound.set_volume(self.mechanical_volume * self.master_volume)

    def _load_mechanical_sounds(self):
        """Load the selected switch profile from sounds/mechanical/<profile>."""
        with self._lock:
            loaded_sounds = self._build_mechanical_sounds(self.mechanical_profile)
            self.mechanical_sounds = loaded_sounds

    def set_mechanical_profile(self, profile):
        """Switch profiles live; keep the current pack if the new one fails."""
        profile = str(profile).strip().lower()
        if profile not in {"blue", "red", "brown", "black"}:
            raise ValueError(f"Unsupported mechanical profile: {profile}")

        with self._lock:
            profile_dir = self.mechanical_dir / profile
            print(f"[SoundKeys Engine] Loading profile {profile!r} from: {profile_dir}")
            # Build first, then atomically replace the active sound dictionary.
            # This avoids leaving the engine with an empty/partial pack on failure.
            loaded_sounds = self._build_mechanical_sounds(profile)
            self.mechanical_sounds = loaded_sounds
            self.mechanical_profile = profile
            config.MECHANICAL_PROFILE = profile
            self._profile_debug_pending = True
            print(
                f"[SoundKeys Engine] Active profile is now {self.mechanical_profile!r}; "
                f"loaded sound keys={sorted(self.mechanical_sounds)}"
            )

    def start(self, mode=None):
        with self._lock:
            if self._closed:
                raise RuntimeError("This SoundKeys engine has already been closed.")
            if self.running:
                return
            if mode is not None:
                normalized = mode.lower().replace(" mode", "")
                if normalized not in {"chaos", "custom", "mechanical"}:
                    raise ValueError(f"Unsupported mode: {mode}")
                self.mode = normalized

            self._load_mappings()
            self._load_sounds()

            if self.mode == "custom":
                for key, filename in self.custom_assignments.items():
                    if filename.lower() not in self.sounds:
                        raise FileNotFoundError(
                            f"Sound '{filename}' assigned to '{key}' was not found."
                        )
            elif self.mode == "chaos":
                if not any(name != self.enter_filename for name in self.sounds):
                    raise RuntimeError("No random Chaos Mode sounds are available.")
            elif self.mode == "mechanical":
                self._load_mechanical_sounds()

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
        # Flip the gate first so no new key event can start another sound.
        with self._lock:
            was_running = self.running
            self.running = False
            hook = self._hook
            self._hook = None

        # These operations can take time on some Windows audio/keyboard-hook
        # configurations, so never perform them while holding the shared lock.
        try:
            pygame.mixer.stop()
        except pygame.error:
            pass

        if hook is not None:
            try:
                keyboard.unhook(hook)
            except (KeyError, ValueError):
                pass
        if was_running and self._on_status_change:
            self._on_status_change(False)

    def toggle_mute(self):
        # Change the logical state immediately. Do not hold the engine lock
        # while asking SDL to stop playback; keyboard callbacks need this lock.
        with self._lock:
            self.muted = not self.muted
            muted = self.muted
        if muted:
            try:
                pygame.mixer.stop()
            except pygame.error:
                # The mixer may be shutting down; the muted state is still valid.
                pass
        return muted

    def _play(self, sound):
        with self._lock:
            if not self.running or self.muted or self._closed:
                return
            channel = pygame.mixer.find_channel(False)
            if channel is not None:
                channel.play(sound)

    def _play_mechanical_key(self, key):
        special_name = self.MECHANICAL_SPECIAL_KEYS.get(key)
        sound_name = special_name if special_name in self.mechanical_sounds else "key"
        sound = self.mechanical_sounds.get(special_name) if special_name else None
        if sound is None:
            sound = self.mechanical_sounds.get("key")
        if self._profile_debug_pending:
            print(
                f"[SoundKeys Engine] First key after switch: profile={self.mechanical_profile!r}, "
                f"pressed={key!r}, sound={sound_name!r}"
            )
            self._profile_debug_pending = False
        if sound is None:
            # If key.wav is absent, use the first available sound as a safe fallback.
            sound = next(iter(self.mechanical_sounds.values()), None)
        if sound is not None:
            self._play(sound)

    def _on_key_press(self, event):
        # Ignore key-release events and invalid keyboard events.
        if getattr(event, "event_type", None) != "down":
            return

        event_name = getattr(event, "name", None)

        if not event_name:
            return

        key = str(event_name).lower()

        # Global mute shortcut (F8).
        if key == self.mute_key:
            self.toggle_mute()
            return

        # Do nothing when SoundKeys is stopped.
        if not self.running:
            return

        # ==========================================
        # CHAOS MODE
        # ==========================================
        if self.mode == "chaos":

            # Enter plays the dedicated Enter sound.
            if key == self.enter_key:
                sound = self.sounds.get(self.enter_filename)

                if sound:
                    self._play(sound)

                return

            # Configured keys trigger random sounds.
            if key in self.trigger_keys:
                choices = [
                    sound
                    for name, sound in self.sounds.items()
                    if name != self.enter_filename
                ]

                if choices:
                    self._play(random.choice(choices))

        # ==========================================
        # CUSTOM MODE
        # ==========================================
        elif self.mode == "custom":

            filename = self.custom_assignments.get(key)

            if filename:
                sound = self.sounds.get(filename.lower())

                if sound:
                    self._play(sound)

        # ==========================================
        # MECHANICAL MODE
        # ==========================================
        elif self.mode == "mechanical":

            self._play_mechanical_key(key)
    def close(self):
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self.stop()
        pygame.mixer.quit()
