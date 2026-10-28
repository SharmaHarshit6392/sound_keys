import pygame
import time

pygame.mixer.init()

# Create two short test sounds with different frequencies.
def create_tone(frequency, duration=0.25, volume=0.4):
    sample_rate = 44100
    sample_count = int(sample_rate * duration)

    import math
    import array

    samples = array.array(
        "h",
        (
            int(
                32767
                * volume
                * math.sin(2 * math.pi * frequency * i / sample_rate)
            )
            for i in range(sample_count)
        ),
    )

    return pygame.mixer.Sound(buffer=samples.tobytes())


low_tone = create_tone(400)
high_tone = create_tone(900)

print("Playing two overlapping sounds...")

low_tone.play()
time.sleep(0.05)
high_tone.play()

time.sleep(0.5)

pygame.mixer.quit()
print("Audio test complete!")