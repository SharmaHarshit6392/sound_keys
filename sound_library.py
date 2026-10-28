import json
import shutil
from pathlib import Path

import pygame


class SoundLibrary:
    """Manage imported audio files without altering their originals."""

    def __init__(self):
        self.root = Path(__file__).resolve().parent
        self.library_dir = self.root / "sounds" / "custom"
        self.index_file = self.root / "library.json"

        self.library_dir.mkdir(parents=True, exist_ok=True)

        self.sounds = self._load_index()

    def _load_index(self):
        """Load the saved library, recovering gracefully from bad JSON."""
        if not self.index_file.exists():
            return []

        try:
            data = json.loads(
                self.index_file.read_text(encoding="utf-8")
            )

            if not isinstance(data, list):
                return []

            return [
                name for name in data
                if isinstance(name, str)
                and Path(name).name == name
                and (self.library_dir / name).is_file()
            ]

        except (OSError, json.JSONDecodeError):
            return []

    def _save_index(self):
        """Persist the library's filenames."""
        self.index_file.write_text(
            json.dumps(self.sounds, indent=2),
            encoding="utf-8"
        )

    def list_sounds(self):
        """Return the names of imported sounds."""
        return list(self.sounds)

    def import_files(self, file_paths):
        """Copy selected audio files into the library."""
        imported = []
        supported = {".mp3", ".wav", ".ogg", ".flac"}

        for source_name in file_paths:
            source = Path(source_name).expanduser().resolve()

            if not source.is_file():
                raise FileNotFoundError(
                    f"File not found: {source}"
                )

            if source.suffix.lower() not in supported:
                continue

            destination = self.library_dir / source.name

            # Avoid overwriting an existing library file.
            if destination.exists():
                stem = source.stem
                suffix = source.suffix
                number = 2

                while destination.exists():
                    destination = (
                        self.library_dir
                        / f"{stem} ({number}){suffix}"
                    )
                    number += 1

            shutil.copy2(source, destination)

            self.sounds.append(destination.name)
            imported.append(destination.name)

        self._save_index()
        return imported

    def remove_sound(self, filename):
        """Remove a library entry and its internal copy only."""
        if filename not in self.sounds:
            return False

        internal_file = self.library_dir / filename

        # Ensure the path cannot escape the library folder.
        if internal_file.parent.resolve() != self.library_dir.resolve():
            raise ValueError("Invalid library filename.")

        self.sounds.remove(filename)
        self._save_index()

        if internal_file.is_file():
            internal_file.unlink()

        return True

    def preview(self, filename):
        """Preview an imported sound."""
        if filename not in self.sounds:
            raise ValueError("This sound is not in the library.")

        path = self.library_dir / filename

        if not path.is_file():
            raise FileNotFoundError(path)

        if not pygame.mixer.get_init():
            pygame.mixer.init()

        sound = pygame.mixer.Sound(str(path))
        sound.play()
        return sound