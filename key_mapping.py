import json
import os
from pathlib import Path


class KeyMapping:
    """Persist key-to-sound assignments, including built-in sounds."""

    VALID_KEYS = (
        set("abcdefghijklmnopqrstuvwxyz")
        | set("0123456789")
        | {
            "enter", "space", "tab", "backspace", "delete",
            "up", "down", "left", "right", "home", "end",
            "page up", "page down", "insert"
        }
        | {f"f{i}" for i in range(1, 13)}
    )

    def __init__(self, sound_library):
        self.root = Path(__file__).resolve().parent
        local_app_data = Path(
            os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
        )
        self.user_data_dir = local_app_data / "SoundKeys"
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self.mapping_file = self.user_data_dir / "key_mappings.json"
        legacy_mapping = self.root / "key_mappings.json"
        if not self.mapping_file.exists() and legacy_mapping.is_file():
            import shutil
            shutil.copy2(legacy_mapping, self.mapping_file)
        self.sound_library = sound_library
        self.mappings = self._load_mappings()

    def _available_sounds(self):
        supported = {".mp3", ".wav", ".ogg", ".flac"}
        result = set()
        for folder in (
            self.root / "sounds" / "chaos",
            self.sound_library.library_dir,
        ):
            if folder.exists():
                result.update(
                    p.name for p in folder.iterdir()
                    if p.is_file() and p.suffix.lower() in supported
                )
        return result

    def _load_mappings(self):
        if self.mapping_file.exists():
            try:
                data = json.loads(self.mapping_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    valid_sounds = self._available_sounds()
                    return {
                        key.lower(): filename
                        for key, filename in data.items()
                        if isinstance(key, str)
                        and isinstance(filename, str)
                        and key.lower() in self.VALID_KEYS
                        and Path(filename).name == filename
                        and filename in valid_sounds
                    }
            except (OSError, json.JSONDecodeError) as error:
                print(f"Mapping load error: {error}")

        import config
        return {
            key.lower(): filename
            for key, filename in config.CUSTOM_KEY_SOUNDS.items()
            if key.lower() in self.VALID_KEYS
        }

    def save(self):
        self.mapping_file.write_text(
            json.dumps(self.mappings, indent=4), encoding="utf-8"
        )

    def assign(self, key, filename):
        key = key.lower().strip()
        if key not in self.VALID_KEYS:
            raise ValueError(f"Unsupported keyboard key: {key}")
        if filename not in self._available_sounds():
            raise ValueError("Selected sound is not present in the built-in or custom SoundKeys library.")
        self.mappings[key] = filename
        self.save()

    def remove(self, key):
        key = key.lower().strip()
        if key not in self.mappings:
            return False
        del self.mappings[key]
        self.save()
        return True

    def list_mappings(self):
        return dict(self.mappings)

    def get_sound(self, key):
        return self.mappings.get(key.lower().strip())
