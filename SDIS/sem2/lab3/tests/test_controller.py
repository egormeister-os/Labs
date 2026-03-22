from __future__ import annotations

from pathlib import Path

from reversi.config import load_app_config, load_help_text
from reversi.controller import GameMode, ReversiController, ScreenState
from reversi.leaderboard import Leaderboard
from reversi.model import Player, ReversiGame


def build_controller(project_dir: Path) -> ReversiController:
    config = load_app_config(project_dir)
    leaderboard = Leaderboard(config.leaderboard_path, config.leaderboard_size)
    help_text = load_help_text(config.help_path)
    return ReversiController(config, leaderboard, help_text)


def test_controller_navigation(project_dir: Path) -> None:
    controller = build_controller(project_dir)

    controller.open_mode_select()
    assert controller.screen is ScreenState.MODE_SELECT
    controller.open_help()
    assert controller.screen is ScreenState.HELP
    controller.open_records()
    assert controller.screen is ScreenState.RECORDS
    controller.open_menu()
    assert controller.screen is ScreenState.MENU


def test_local_two_player_keeps_board_orientation(project_dir: Path) -> None:
    controller = build_controller(project_dir)
    controller.start_mode(GameMode.LOCAL_TWO)

    first = controller.handle_board_move(2, 3, now_ms=0)
    second = controller.handle_board_move(2, 2, now_ms=10)

    assert first is not None
    assert second is not None
    assert controller.current_orientation() is Player.BLACK
    assert controller.board_coords_from_display(0, 0) == (0, 0)


def test_ai_mode_makes_response_move(project_dir: Path) -> None:
    controller = build_controller(project_dir)
    controller.start_mode(GameMode.VS_AI)

    player_move = controller.handle_board_move(2, 3, now_ms=0)
    ai_move = controller.update(200)

    assert player_move is not None
    assert ai_move is not None
    assert controller.game.current_player is Player.BLACK


def test_controller_passes_turn_when_needed(project_dir: Path) -> None:
    controller = build_controller(project_dir)
    controller.start_mode(GameMode.PRACTICE)
    controller.game.load_board(
        [
            "BBBBBBBB",
            "BBBBBBBB",
            "BBBBBBBB",
            "BBBBBBBB",
            "BBBBBBBB",
            "BBBBBBBB",
            "BBBBBBBB",
            "BBBBBBW.",
        ]
    )
    controller.game.current_player = Player.WHITE

    outcome = controller.update(0)

    assert outcome is not None
    assert controller.game.current_player is Player.BLACK
    assert "пропущен" in controller.status_message


def test_controller_prompts_for_new_record_and_saves(project_dir: Path) -> None:
    controller = build_controller(project_dir)
    controller.start_mode(GameMode.PRACTICE)
    controller.game.load_board(
        [
            "BBBBBBBB",
            "BBBBBBBB",
            "BBBBBBBB",
            "BBBBBBBB",
            "WWWWWWWW",
            "WWWWWWWW",
            "WWWWWWWW",
            "WWWWWWWB",
        ]
    )
    controller.game.game_over = True
    controller.update(0)

    assert controller.prompt.active is True
    assert controller.prompt.purpose == "save_name"
    assert controller.submit_name("Tester") is True
    assert controller.leaderboard.entries[0].name == "Tester"


def test_online_join_asks_for_address_and_connects(project_dir: Path, monkeypatch) -> None:
    controller = build_controller(project_dir)
    called = {}

    def fake_connect(self) -> None:
        called["connected"] = (self.host, self.port)

    monkeypatch.setattr("reversi.network.OnlineClient.connect", fake_connect)
    controller.start_mode(GameMode.ONLINE_JOIN)

    assert controller.prompt.active is True
    controller.connect_to_host("10.0.0.1:6000")

    assert controller.screen is ScreenState.WAITING
    assert called["connected"] == ("10.0.0.1", 6000)


def test_controller_submit_name_without_pending_score(project_dir: Path) -> None:
    controller = build_controller(project_dir)

    assert controller.submit_name("Nobody") is False


def test_controller_open_menu_closes_network(project_dir: Path) -> None:
    controller = build_controller(project_dir)

    class StubConnection:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    controller.server = StubConnection()
    controller.client = StubConnection()
    controller.open_menu()

    assert controller.server is None
    assert controller.client is None


def test_controller_online_host_update_switches_to_game(project_dir: Path) -> None:
    controller = build_controller(project_dir)

    class StubServer:
        def __init__(self) -> None:
            self.accepted = False
            self.sent = 0

        def accept_client(self) -> bool:
            if not self.accepted:
                self.accepted = True
                return True
            return False

        def send_state(self, _game) -> None:
            self.sent += 1

        def poll_client(self, _game) -> bool:
            return False

        def close(self) -> None:
            return None

    controller.mode = GameMode.ONLINE_HOST
    controller.game = ReversiGame(controller.config.board_size)
    controller.screen = ScreenState.WAITING
    controller.server = StubServer()

    controller.update(0)

    assert controller.screen is ScreenState.GAME
    assert controller.server.sent == 1


def test_controller_online_join_update_applies_state(project_dir: Path) -> None:
    controller = build_controller(project_dir)
    controller.mode = GameMode.ONLINE_JOIN
    controller.game = ReversiGame(controller.config.board_size)

    class StubClient:
        def poll_messages(self, game) -> bool:
            game.apply_move(2, 3)
            return True

        def close(self) -> None:
            return None

    controller.client = StubClient()

    controller.update(0)

    assert controller.screen is ScreenState.GAME
    assert "Состояние игры обновлено" in controller.status_message


def test_controller_local_turn_logic(project_dir: Path) -> None:
    controller = build_controller(project_dir)

    assert controller.is_local_turn() is False
    controller.start_mode(GameMode.VS_AI)
    assert controller.is_local_turn() is True
    controller.handle_board_move(2, 3, 0)
    assert controller.is_local_turn() is False


def test_controller_online_orientation_still_rotates(project_dir: Path) -> None:
    controller = build_controller(project_dir)
    controller.mode = GameMode.ONLINE_JOIN
    controller.game = ReversiGame(controller.config.board_size)
    controller.game.current_player = Player.WHITE

    assert controller.current_orientation() is Player.WHITE
    assert controller.board_coords_from_display(0, 0) == (7, 7)
