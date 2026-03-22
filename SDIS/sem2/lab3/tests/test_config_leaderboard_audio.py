from __future__ import annotations

import wave
from pathlib import Path

import pygame

from reversi.audio import SoundManager, ensure_audio_assets
from reversi.config import AudioConfig, load_app_config, load_help_text
from reversi.leaderboard import Leaderboard


def test_load_config_and_help(project_dir: Path) -> None:
    config = load_app_config(project_dir)
    help_text = load_help_text(config.help_path)

    assert config.window_width == 900
    assert config.help_path.exists()
    assert config.leaderboard_path.exists()
    assert "Test Help" in help_text
    assert "Line one." in help_text


def test_leaderboard_adds_and_sorts_entries(project_dir: Path) -> None:
    path = project_dir / "config" / "leaderboard.json"
    leaderboard = Leaderboard(path, max_entries=3)

    leaderboard.add_entry("New", 45, "vs_ai", played_at="2026-03-22 12:00")
    leaderboard.add_entry("Mid", 30, "practice", played_at="2026-03-22 12:01")
    leaderboard.add_entry("Low", 10, "practice", played_at="2026-03-22 12:02")

    reloaded = Leaderboard(path, max_entries=3)
    assert reloaded.entries[0].name == "New"
    assert len(reloaded.entries) == 3
    assert reloaded.is_new_record(46) is True
    assert reloaded.is_new_record(20) is False


def test_audio_assets_are_generated(project_dir: Path) -> None:
    config = load_app_config(project_dir)

    ensure_audio_assets(config.audio)

    for path in (
        config.audio.music_path,
        config.audio.move_sound_path,
        config.audio.flip_sound_path,
        config.audio.error_sound_path,
        config.audio.win_sound_path,
    ):
        assert path.exists()
        with wave.open(str(path), "rb") as wav:
            assert wav.getnframes() > 0


def test_sound_manager_initializes_and_plays(project_dir: Path, monkeypatch) -> None:
    config = load_app_config(project_dir)
    calls: dict[str, object] = {"played": [], "loaded": None, "music_play": 0, "music_stop": 0}

    class FakeSound:
        def __init__(self, path: str) -> None:
            self.path = path

        def set_volume(self, value: float) -> None:
            calls.setdefault("volumes", []).append(value)

        def play(self) -> None:
            calls["played"].append(self.path)

    class FakeMusic:
        def load(self, path: str) -> None:
            calls["loaded"] = path

        def set_volume(self, value: float) -> None:
            calls["music_volume"] = value

        def play(self, loops: int) -> None:
            calls["music_play"] += loops

        def stop(self) -> None:
            calls["music_stop"] += 1

    class FakeMixer:
        def __init__(self) -> None:
            self.music = FakeMusic()

        def init(self) -> None:
            calls["inited"] = True

        def Sound(self, path: str) -> FakeSound:
            return FakeSound(path)

    fake_mixer = FakeMixer()
    monkeypatch.setattr(pygame, "mixer", fake_mixer)

    manager = SoundManager(config.audio)

    assert manager.initialize() is True
    manager.play_sound("move")
    manager.play_music()
    manager.stop_music()

    assert calls["inited"] is True
    assert str(config.audio.music_path) == calls["loaded"]
    assert calls["played"]
    assert calls["music_play"] == -1
    assert calls["music_stop"] == 1


def test_sound_manager_handles_mixer_failure(project_dir: Path, monkeypatch) -> None:
    config = load_app_config(project_dir)

    class BrokenMixer:
        music = object()

        def init(self) -> None:
            raise pygame.error("no audio")

    monkeypatch.setattr(pygame, "mixer", BrokenMixer())
    manager = SoundManager(config.audio)

    assert manager.initialize() is False

