import random
import threading
from pathlib import Path

import keyboard
import pygame

# ---------- CONFIGURATION ----------

SOUND_DIR = Path(__file__).parent / "sounds" / "chaos"

TRIGGER_KEYS = {"a", "s", "d", "space"}
SPECIAL_SOUND_KEY = "enter"
SPECIAL_SOUND_FILE = "fahhh.mp3"

MAX_SIMULTANEOUS_SOUNDS = 8

# ---------- AUDIO ENGINE ----------

pygame.mixer.init()
pygame.mixer.set_num_channels(MAX_SIMULTANEOUS_SOUNDS)

sounds = []

for file_path in SOUND_DIR.glob("*.mp3"):
    try:
        sounds.append((file_path.name, pygame.mixer.Sound(str(file_path))))
    except pygame.error as error:
        print(f"Could not load {file_path.name}: {error}")

special_sound = next(
    (
        sound
        for name, sound in sounds
        if name.lower() == SPECIAL_SOUND_FILE.lower()
    ),
    None,
)

if special_sound is None:
    raise FileNotFoundError(
        f"Could not find {SPECIAL_SOUND_FILE} in {SOUND_DIR}"
    )

chaos_sounds = [
    sound for name, sound in sounds
    if name.lower() != SPECIAL_SOUND_FILE.lower()
]

if not chaos_sounds:
    raise RuntimeError("Add at least one other MP3 file to the chaos folder.")

audio_lock = threading.Lock()

def play_sound(sound):
    with audio_lock:
        available_channel = pygame.mixer.find_channel(False)

        if available_channel is not None:
            available_channel.play(sound)

def on_key_press(event):
    if event.event_type != "down" or event.is_keypad:
        return

    key = event.name

    if key == SPECIAL_SOUND_KEY:
        play_sound(special_sound)

    elif key in TRIGGER_KEYS:
        play_sound(random.choice(chaos_sounds))

# ---------- START ----------

print("SoundKeys Chaos Mode is running!")
print("A / S / D / Space : Random chaos sounds")
print("Enter             : fahhh.mp3")
print("Esc               : Exit")

keyboard.on_press(on_key_press)

try:
    keyboard.wait("esc")
finally:
    keyboard.unhook_all()
    pygame.mixer.quit()
    print("SoundKeys stopped.")