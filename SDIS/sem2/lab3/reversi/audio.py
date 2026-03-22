from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

import pygame

from reversi.config import AudioConfig


def _write_wave(path: Path, samples: list[int], sample_rate: int = 44100) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(sample_rate)
        frames = b"".join(struct.pack("<h", sample) for sample in samples)
        file.writeframes(frames)


def _sine_wave(
    frequency: float,
    duration: float,
    volume: float = 0.45,
    sample_rate: int = 44100,
) -> list[int]:
    count = int(sample_rate * duration)
    samples: list[int] = []
    for index in range(count):
        angle = 2 * math.pi * frequency * (index / sample_rate)
        value = int(32767 * volume * math.sin(angle))
        samples.append(value)
    return samples


def _mix(parts: list[list[int]]) -> list[int]:
    if not parts:
        return []
    length = max(len(part) for part in parts)
    mixed = []
    for index in range(length):
        value = sum(part[index] if index < len(part) else 0 for part in parts)
        mixed.append(max(-32767, min(32767, value)))
    return mixed


def ensure_audio_assets(audio: AudioConfig) -> None:
    if not audio.move_sound_path.exists():
        _write_wave(audio.move_sound_path, _sine_wave(440, 0.12))
    if not audio.flip_sound_path.exists():
        _write_wave(audio.flip_sound_path, _mix([_sine_wave(660, 0.1, 0.25), _sine_wave(880, 0.1, 0.2)]))
    if not audio.error_sound_path.exists():
        _write_wave(audio.error_sound_path, _mix([_sine_wave(240, 0.08, 0.4), _sine_wave(200, 0.08, 0.35)]))
    if not audio.win_sound_path.exists():
        _write_wave(
            audio.win_sound_path,
            _mix([
                _sine_wave(523.25, 0.3, 0.18),
                _sine_wave(659.25, 0.3, 0.18),
                _sine_wave(783.99, 0.3, 0.18),
            ]),
        )
    if not audio.music_path.exists():
        melody = []
        for frequency in (261.63, 329.63, 392.0, 523.25, 392.0, 329.63):
            melody.extend(_sine_wave(frequency, 0.25, 0.10))
        _write_wave(audio.music_path, melody)


class SoundManager:
    def __init__(self, audio: AudioConfig) -> None:
        self.audio = audio
        self.enabled = False
        self.sounds: dict[str, object] = {}

    def initialize(self) -> bool:
        ensure_audio_assets(self.audio)
        try:
            pygame.mixer.init()
            self.sounds = {
                "move": pygame.mixer.Sound(str(self.audio.move_sound_path)),
                "flip": pygame.mixer.Sound(str(self.audio.flip_sound_path)),
                "error": pygame.mixer.Sound(str(self.audio.error_sound_path)),
                "win": pygame.mixer.Sound(str(self.audio.win_sound_path)),
            }
            for sound in self.sounds.values():
                sound.set_volume(self.audio.sound_volume)
            pygame.mixer.music.load(str(self.audio.music_path))
            pygame.mixer.music.set_volume(self.audio.music_volume)
            self.enabled = True
        except pygame.error:
            self.enabled = False
        return self.enabled

    def play_sound(self, name: str) -> None:
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def play_music(self) -> None:
        if self.enabled:
            pygame.mixer.music.play(-1)

    def stop_music(self) -> None:
        if self.enabled:
            pygame.mixer.music.stop()

