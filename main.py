
import random
import threading
from pathlib import Path

import keyboard
import pygame

import config

# ---------- CONFIGURATION ----------

SOUND_DIR = Path(__file__).parent / "sounds" / "chaos"

MODE = config.MODE.lower()
TRIGGER_KEYS = {key.lower() for key in config.CHAOS_TRIGGER_KEYS}
SPECIAL_SOUND_KEY = "enter"
SPECIAL_SOUND_FILE = config.ENTER_SOUND
MUTE_KEY = config.MUTE_KEY.lower()
MAX_SIMULTANEOUS_SOUNDS = config.MAX_SIMULTANEOUS_SOUNDS

if MODE not in {"chaos", "custom"}:
    raise ValueError("MODE must be either 'chaos' or 'custom'.")

# ---------- AUDIO ENGINE ----------

pygame.mixer.init()
pygame.mixer.set_num_channels(MAX_SIMULTANEOUS_SOUNDS)

sounds = {}

try:
    for file_path in SOUND_DIR.glob("*.mp3"):
        try:
            sounds[file_path.name.lower()] = pygame.mixer.Sound(
                str(file_path)
            )
        except pygame.error as error:
            print(f"Could not load {file_path.name}: {error}")

    # Check the special Enter sound.
    if SPECIAL_SOUND_FILE.lower() not in sounds:
        raise FileNotFoundError(
            f"Could not find '{SPECIAL_SOUND_FILE}' in {SOUND_DIR}"
        )

    special_sound = sounds[SPECIAL_SOUND_FILE.lower()]

    # Exclude the Enter sound from random Chaos Mode sounds.
    chaos_sounds = [
        sound
        for filename, sound in sounds.items()
        if filename != SPECIAL_SOUND_FILE.lower()
    ]

    if MODE == "chaos" and not chaos_sounds:
        raise RuntimeError(
            "Add at least one other MP3 to the sounds/chaos folder."
        )

    # Prepare key-to-sound assignments for Custom Mode.
    custom_sounds = {}

    if MODE == "custom":
        for key, filename in config.CUSTOM_KEY_SOUNDS.items():
            filename = filename.lower()

            if filename not in sounds:
                raise FileNotFoundError(
                    f"Custom sound '{filename}' assigned to '{key}' "
                    f"was not found in {SOUND_DIR}."
                )

            custom_sounds[key.lower()] = sounds[filename]

except Exception:
    pygame.mixer.quit()
    raise

# ---------- PLAYBACK AND MUTE ----------

audio_lock = threading.Lock()
muted = False


def play_sound(sound):
    with audio_lock:
        if muted:
            return

        channel = pygame.mixer.find_channel(False)

        # Skip the sound if every channel is busy.
        if channel is not None:
            channel.play(sound)


def toggle_mute():
    global muted

    with audio_lock:
        muted = not muted
        current_state = muted

        if current_state:
            pygame.mixer.stop()

    print(
        "SoundKeys MUTED"
        if current_state
        else "SoundKeys UNMUTED"
    )


# ---------- KEYBOARD HANDLER ----------

def on_key_press(event):
    if event.event_type != "down":
        return

    key = event.name.lower()

    if key == MUTE_KEY:
        toggle_mute()
        return

    if key == "esc":
        return

    # Enter always plays its dedicated sound.
    if key == SPECIAL_SOUND_KEY:
        play_sound(special_sound)
        return

    if MODE == "chaos":
        if key in TRIGGER_KEYS:
            play_sound(random.choice(chaos_sounds))

    elif MODE == "custom":
        sound = custom_sounds.get(key)

        if sound is not None:
            play_sound(sound)


# ---------- START ----------

print(f"SoundKeys {MODE.title()} Mode is running!")

if MODE == "chaos":
    print("A / S / D / Space : Random chaos sounds")
else:
    print("Custom key assignments:")
    for key, filename in config.CUSTOM_KEY_SOUNDS.items():
        print(f"  {key} -> {filename}")

print("Enter : Dedicated sound")
print(f"{MUTE_KEY.upper()} : Toggle mute")
print("Esc : Exit")

keyboard.on_press(on_key_press)

try:
    keyboard.wait("esc")
finally:
    keyboard.unhook_all()
    pygame.mixer.quit()
    print("SoundKeys stopped.")
