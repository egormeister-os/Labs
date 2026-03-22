from __future__ import annotations

from reversi.ai import GreedyAI
from reversi.model import Player, ReversiGame


def test_ai_returns_none_when_no_moves() -> None:
    game = ReversiGame(4)
    game.load_board(
        [
            "BBBB",
            "BBBB",
            "BBBB",
            "BBBB",
        ]
    )
    game.current_player = Player.WHITE

    assert GreedyAI().choose_move(game, Player.WHITE) is None


def test_ai_prefers_corner_move() -> None:
    game = ReversiGame(4)
    game.load_board(
        [
            ".WB.",
            "WWB.",
            "BBW.",
            "....",
        ]
    )
    game.current_player = Player.BLACK

    assert GreedyAI().choose_move(game, Player.BLACK) == (0, 0)

