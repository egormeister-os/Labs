from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


Color = tuple[int, int, int]


@dataclass(frozen=True)
class AudioConfig:
    backend: str
    music_path: Path
    move_sound_path: Path
    flip_sound_path: Path
    error_sound_path: Path
    win_sound_path: Path
    music_volume: float
    sound_volume: float


@dataclass(frozen=True)
class NetworkConfig:
    host: str
    port: int
    backlog: int
    connect_timeout: float


@dataclass(frozen=True)
class ThemeConfig:
    background_color: Color
    panel_color: Color
    accent_color: Color
    board_color: Color
    grid_color: Color
    black_disc_color: Color
    white_disc_color: Color
    hint_color: Color
    text_color: Color
    warning_color: Color


@dataclass(frozen=True)
class AppConfig:
    base_dir: Path
    window_width: int
    window_height: int
    fps: int
    board_size: int
    animation_ms: int
    ai_delay_ms: int
    leaderboard_size: int
    help_path: Path
    leaderboard_path: Path
    audio: AudioConfig
    network: NetworkConfig
    theme: ThemeConfig


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _resolve(base_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _color(values: list[int]) -> Color:
    if len(values) != 3:
        raise ValueError("Color must contain exactly three channels")
    return tuple(int(channel) for channel in values)


def load_app_config(base_dir: Path | str) -> AppConfig:
    root = Path(base_dir).resolve()
    raw = _load_json(root / "config" / "app.json")

    audio = raw["audio"]
    theme = raw["theme"]
    network = raw["network"]

    return AppConfig(
        base_dir=root,
        window_width=int(raw["window"]["width"]),
        window_height=int(raw["window"]["height"]),
        fps=int(raw["window"]["fps"]),
        board_size=int(raw["game"]["board_size"]),
        animation_ms=int(raw["game"]["animation_ms"]),
        ai_delay_ms=int(raw["game"]["ai_delay_ms"]),
        leaderboard_size=int(raw["game"]["leaderboard_size"]),
        help_path=_resolve(root, raw["files"]["help"]),
        leaderboard_path=_resolve(root, raw["files"]["leaderboard"]),
        audio=AudioConfig(
            backend=str(audio.get("backend", "auto")),
            music_path=_resolve(root, audio["music_path"]),
            move_sound_path=_resolve(root, audio["move_sound_path"]),
            flip_sound_path=_resolve(root, audio["flip_sound_path"]),
            error_sound_path=_resolve(root, audio["error_sound_path"]),
            win_sound_path=_resolve(root, audio["win_sound_path"]),
            music_volume=float(audio["music_volume"]),
            sound_volume=float(audio["sound_volume"]),
        ),
        network=NetworkConfig(
            host=str(network["host"]),
            port=int(network["port"]),
            backlog=int(network["backlog"]),
            connect_timeout=float(network["connect_timeout"]),
        ),
        theme=ThemeConfig(
            background_color=_color(theme["background_color"]),
            panel_color=_color(theme["panel_color"]),
            accent_color=_color(theme["accent_color"]),
            board_color=_color(theme["board_color"]),
            grid_color=_color(theme["grid_color"]),
            black_disc_color=_color(theme["black_disc_color"]),
            white_disc_color=_color(theme["white_disc_color"]),
            hint_color=_color(theme["hint_color"]),
            text_color=_color(theme["text_color"]),
            warning_color=_color(theme["warning_color"]),
        ),
    )


def load_help_text(path: Path | str) -> str:
    raw = _load_json(Path(path))
    title = raw.get("title", "Reversi")
    lines = raw.get("lines", [])
    return "\n".join([title, ""] + [str(line) for line in lines])
