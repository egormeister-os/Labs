from __future__ import annotations

from pathlib import Path

import pygame

import main
from reversi.model import MoveOutcome, Player
from reversi.controller import GameMode, PromptState, ScreenState
from reversi.ui import Button, PygameReversiApp, oriented_position, render_text, wrap_text


def test_wrap_text_and_orientation_helpers() -> None:
    assert wrap_text("one two three", 7) == ["one two", "three"]
    assert wrap_text("superlongword", 3) == ["superlongword"]
    assert oriented_position(8, 0, 0, Player.BLACK) == (0, 0)
    assert oriented_position(8, 0, 0, Player.WHITE) == (7, 7)


def test_button_contains_point() -> None:
    button = Button("Test", pygame.Rect(10, 10, 40, 30), "noop")
    assert button.contains((20, 20)) is True
    assert button.contains((0, 0)) is False


def test_render_text_fallback(monkeypatch) -> None:
    class BrokenFont:
        def SysFont(self, *_args, **_kwargs):
            raise RuntimeError("broken")

    monkeypatch.setattr(pygame, "font", BrokenFont())
    surface = render_text("abc", 20, (255, 255, 255))

    assert isinstance(surface, pygame.Surface)
    assert surface.get_width() > 0


def test_ui_draw_and_actions(project_dir: Path) -> None:
    app = PygameReversiApp(project_dir)
    pygame.display.set_mode((app.config.window_width, app.config.window_height))
    app.screen = pygame.display.get_surface()

    app.draw(0)
    assert app.buttons
    app._handle_action("start")
    assert app.controller.screen is ScreenState.MODE_SELECT
    app.draw(0)
    app._handle_action("records")
    assert app.controller.screen is ScreenState.RECORDS
    app.draw(0)
    app._handle_action("help")
    assert app.controller.screen is ScreenState.HELP
    app.draw(0)
    app._handle_action("back")
    assert app.controller.screen is ScreenState.MENU
    app.draw(0)
    app._handle_action(f"mode:{GameMode.PRACTICE.value}")
    assert app.controller.screen is ScreenState.GAME
    app.draw(0)
    assert app._board_position_from_mouse((50, 130)) == (0, 0)
    assert app._board_position_from_mouse((5, 5)) is None

    app.pending_animation = MoveOutcome(Player.BLACK, (2, 3), [(3, 3)], Player.WHITE, None, False)
    app.animation_started_at = 0
    app.draw(120)

    app.controller.open_help()
    app.draw(0)
    app.controller.open_records()
    app.draw(0)
    app.controller.screen = ScreenState.WAITING
    app.draw(0)

    quit_events = []
    original_post = pygame.event.post
    pygame.event.post = lambda event: quit_events.append(event.type)
    try:
        app._handle_action("exit")
    finally:
        pygame.event.post = original_post
    assert quit_events == [pygame.QUIT]


def test_ui_prompt_submission_and_event_handling(project_dir: Path) -> None:
    app = PygameReversiApp(project_dir)
    pygame.display.set_mode((app.config.window_width, app.config.window_height))
    app.screen = pygame.display.get_surface()
    app.controller.awaiting_name_score = 50
    app.controller.awaiting_name_mode = "practice"
    app.controller.prompt = PromptState(True, "Record", "Name", "save_name")
    app.input_text = "Player"

    app._submit_prompt()

    assert app.controller.leaderboard.entries[0].name == "Player"

    app.controller.prompt = PromptState(True, "Join", "127.0.0.1:50007", "join_address")
    app.input_text = "127.0.0.1:50007"

    class FakeClient:
        def __init__(self) -> None:
            self.connected = False

    original_connect = app.controller.connect_to_host

    called = {}

    def fake_connect(value: str) -> None:
        called["value"] = value

    app.controller.connect_to_host = fake_connect
    app._submit_prompt()
    assert called["value"] == "127.0.0.1:50007"
    app.controller.connect_to_host = original_connect

    app.controller.open_menu()
    app.draw(0)
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": app.buttons[0].rect.center})
    app.handle_event(event, 0)
    assert app.controller.screen is ScreenState.MODE_SELECT

    app.controller.prompt = PromptState(True, "Join", "127.0.0.1:50007", "join_address")
    key_event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_BACKSPACE, "unicode": ""})
    app.input_text = "abc"
    app.handle_event(key_event, 0)
    assert app.input_text == "ab"

    text_event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_a, "unicode": "x"})
    app.handle_event(text_event, 0)
    assert app.input_text == "abx"

    app.controller.prompt = PromptState()
    esc_event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE, "unicode": ""})
    app.handle_event(esc_event, 0)
    assert app.controller.screen is ScreenState.MENU

    app.controller.start_mode(GameMode.PRACTICE)
    app.draw(0)
    app.sound_manager.play_sound = lambda _name: None
    game_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (320, 320)})
    app.handle_event(game_click, 0)
    assert app.pending_animation is not None


def test_ui_setup_and_register_animation(project_dir: Path, monkeypatch) -> None:
    app = PygameReversiApp(project_dir)
    music_calls = {"init": 0, "music": 0, "win": 0}
    monkeypatch.setattr(app.sound_manager, "initialize", lambda: music_calls.__setitem__("init", music_calls["init"] + 1) or True)
    monkeypatch.setattr(app.sound_manager, "play_music", lambda: music_calls.__setitem__("music", music_calls["music"] + 1))
    monkeypatch.setattr(app.sound_manager, "play_sound", lambda name: music_calls.__setitem__(name, music_calls.get(name, 0) + 1))

    app.setup()
    assert app.screen is not None
    assert music_calls["init"] == 1
    assert music_calls["music"] == 1

    outcome = MoveOutcome(Player.BLACK, (0, 0), [], Player.WHITE, None, True)
    app._register_animation(outcome, 123)
    assert app.animation_started_at == 123
    assert music_calls["win"] == 1


def test_main_calls_run_app(monkeypatch, project_dir: Path) -> None:
    called = {}

    def fake_run(base_dir: Path) -> None:
        called["base_dir"] = base_dir

    monkeypatch.setattr(main, "run_app", fake_run)
    main.main()

    assert called["base_dir"].name == "lab3"
