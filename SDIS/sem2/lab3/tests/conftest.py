from __future__ import annotations

import json
import os
from pathlib import Path

import pygame
import pytest


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


@pytest.fixture(scope="session", autouse=True)
def pygame_runtime() -> None:
    pygame.init()
    pygame.display.set_mode((8, 8))
    yield
    pygame.quit()


@pytest.fixture()
def project_dir(tmp_path: Path) -> Path:
    (tmp_path / "config").mkdir()
    (tmp_path / "assets" / "audio").mkdir(parents=True)

    app_config = {
        "window": {"width": 900, "height": 760, "fps": 60},
        "game": {"board_size": 8, "animation_ms": 200, "ai_delay_ms": 100, "leaderboard_size": 10},
        "files": {"help": "config/help.json", "leaderboard": "config/leaderboard.json"},
        "audio": {
            "backend": "auto",
            "music_path": "assets/audio/music.wav",
            "move_sound_path": "assets/audio/move.wav",
            "flip_sound_path": "assets/audio/flip.wav",
            "error_sound_path": "assets/audio/error.wav",
            "win_sound_path": "assets/audio/win.wav",
            "music_volume": 0.3,
            "sound_volume": 0.5,
        },
        "network": {"host": "127.0.0.1", "port": 50007, "backlog": 1, "connect_timeout": 1.0},
        "theme": {
            "background_color": [10, 20, 30],
            "panel_color": [40, 60, 80],
            "accent_color": [200, 180, 70],
            "board_color": [0, 120, 80],
            "grid_color": [220, 240, 230],
            "black_disc_color": [15, 15, 15],
            "white_disc_color": [245, 245, 235],
            "hint_color": [255, 210, 90],
            "text_color": [250, 250, 245],
            "warning_color": [255, 150, 100],
        },
    }
    help_text = {
        "title": "Test Help",
        "lines": [
            "Line one.",
            "Line two.",
        ],
    }
    leaderboard = [
        {"name": "Ada", "score": 20, "mode": "practice", "played_at": "2026-03-01 10:00"}
    ]

    (tmp_path / "config" / "app.json").write_text(json.dumps(app_config), encoding="utf-8")
    (tmp_path / "config" / "help.json").write_text(json.dumps(help_text), encoding="utf-8")
    (tmp_path / "config" / "leaderboard.json").write_text(json.dumps(leaderboard), encoding="utf-8")
    return tmp_path
