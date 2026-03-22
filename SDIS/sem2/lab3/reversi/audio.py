from __future__ import annotations

import math
import shutil
import struct
import subprocess
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
    VALID_BACKENDS = {"auto", "pygame", "paplay", "ffplay", "silent"}

    def __init__(self, audio: AudioConfig) -> None:
        self.audio = audio
        self.enabled = False
        self.sounds: dict[str, object] = {}
        self.mixer: object | None = None
        self.backend = "silent"
        self.status_text = "Аудио отключено."
        self.player_command: str | None = None
        self.music_process: subprocess.Popen | None = None
        self.effect_processes: list[subprocess.Popen] = []
        self.music_requested = False
        self._sound_paths = {
            "move": self.audio.move_sound_path,
            "flip": self.audio.flip_sound_path,
            "error": self.audio.error_sound_path,
            "win": self.audio.win_sound_path,
        }

    def initialize(self) -> bool:
        ensure_audio_assets(self.audio)

        requested_backend = self.audio.backend.lower()
        if requested_backend not in self.VALID_BACKENDS:
            requested_backend = "auto"

        for backend in self._backend_order(requested_backend):
            if backend == "pygame" and self._initialize_pygame():
                return True
            if backend in {"paplay", "ffplay"} and self._initialize_external(backend):
                return True
            if backend == "silent":
                break

        self._set_silent("Аудио отключено: рабочий backend не найден.")
        return False

    def play_sound(self, name: str) -> None:
        if not self.enabled:
            return
        if self.backend == "pygame" and name in self.sounds:
            self.sounds[name].play()
            return
        path = self._sound_paths.get(name)
        if path is None:
            return
        process = self._spawn_external_player(path, self.audio.sound_volume, music=False)
        if process is not None:
            self.effect_processes.append(process)

    def play_music(self) -> None:
        self.music_requested = True
        if not self.enabled:
            return
        if self.backend == "pygame" and self.mixer is not None:
            self.mixer.music.play(-1)
            return
        if self.music_process is None:
            self.music_process = self._spawn_external_player(self.audio.music_path, self.audio.music_volume, music=True)

    def stop_music(self) -> None:
        self.music_requested = False
        if self.backend == "pygame" and self.mixer is not None:
            self.mixer.music.stop()
            return
        self._terminate_process(self.music_process)
        self.music_process = None

    def pump(self) -> None:
        self.effect_processes = [process for process in self.effect_processes if process.poll() is None]
        if self.backend in {"paplay", "ffplay"} and self.music_requested:
            if self.music_process is None or self.music_process.poll() is not None:
                self._terminate_process(self.music_process)
                self.music_process = self._spawn_external_player(
                    self.audio.music_path,
                    self.audio.music_volume,
                    music=True,
                )

    def shutdown(self) -> None:
        self.stop_music()
        for process in self.effect_processes:
            self._terminate_process(process)
        self.effect_processes = []

    def _backend_order(self, requested_backend: str) -> list[str]:
        if requested_backend == "auto":
            return ["pygame", "paplay", "ffplay", "silent"]
        if requested_backend == "silent":
            return ["silent"]
        return [requested_backend, "silent"]

    def _initialize_pygame(self) -> bool:
        try:
            mixer = pygame.__dict__.get("mixer")
            if mixer is None or type(mixer).__name__ == "MissingModule":
                return False
            mixer.init()
            self.sounds = {
                "move": mixer.Sound(str(self.audio.move_sound_path)),
                "flip": mixer.Sound(str(self.audio.flip_sound_path)),
                "error": mixer.Sound(str(self.audio.error_sound_path)),
                "win": mixer.Sound(str(self.audio.win_sound_path)),
            }
            for sound in self.sounds.values():
                sound.set_volume(self.audio.sound_volume)
            mixer.music.load(str(self.audio.music_path))
            mixer.music.set_volume(self.audio.music_volume)
            self.mixer = mixer
            self.backend = "pygame"
            self.enabled = True
            self.status_text = "Аудио: pygame mixer."
            return True
        except (AttributeError, ModuleNotFoundError, NotImplementedError, pygame.error):
            self.sounds = {}
            self.mixer = None
            return False

    def _initialize_external(self, backend: str) -> bool:
        command = shutil.which(backend)
        if not command:
            return False
        self.backend = backend
        self.enabled = True
        self.player_command = command
        self.status_text = f"Аудио: системный backend {backend}."
        return True

    def _set_silent(self, status_text: str) -> None:
        self.enabled = False
        self.backend = "silent"
        self.player_command = None
        self.mixer = None
        self.sounds = {}
        self.status_text = status_text

    def _spawn_external_player(
        self,
        path: Path,
        volume: float,
        *,
        music: bool,
    ) -> subprocess.Popen | None:
        if self.player_command is None:
            return None

        command = self._build_external_command(path, volume, music=music)
        try:
            return subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError:
            self._set_silent("Аудио отключено: не удалось запустить системный плеер.")
            return None

    def _build_external_command(self, path: Path, volume: float, *, music: bool) -> list[str]:
        if self.backend == "paplay":
            return [
                self.player_command or "paplay",
                "--client-name=Reversi",
                f"--stream-name={'Reversi Music' if music else 'Reversi Effect'}",
                f"--volume={self._paplay_volume(volume)}",
                str(path),
            ]
        return [
            self.player_command or "ffplay",
            "-nodisp",
            "-autoexit",
            "-loglevel",
            "quiet",
            "-volume",
            str(self._ffplay_volume(volume)),
            str(path),
        ]

    def _paplay_volume(self, volume: float) -> int:
        return max(0, min(65536, int(volume * 65536)))

    def _ffplay_volume(self, volume: float) -> int:
        return max(0, min(100, int(volume * 100)))

    def _terminate_process(self, process: subprocess.Popen | None) -> None:
        if process is None or process.poll() is not None:
            return
        try:
            process.terminate()
            process.wait(timeout=0.2)
        except (OSError, subprocess.TimeoutExpired):
            try:
                process.kill()
            except OSError:
                pass
