from __future__ import annotations

import pytest

from reversi.model import Player, ReversiGame


def test_invalid_board_size_raises() -> None:
    with pytest.raises(ValueError):
        ReversiGame(5)


def test_initial_board_and_legal_moves() -> None:
    game = ReversiGame(8)

    assert game.score_for(Player.BLACK) == 2
    assert game.score_for(Player.WHITE) == 2
    assert set(game.legal_moves()) == {(2, 3), (3, 2), (4, 5), (5, 4)}


def test_apply_move_flips_discs_and_changes_turn() -> None:
    game = ReversiGame(8)

    outcome = game.apply_move(2, 3)

    assert outcome is not None
    assert outcome.player is Player.BLACK
    assert outcome.flipped == [(3, 3)]
    assert game.board[2][3] is Player.BLACK
    assert game.board[3][3] is Player.BLACK
    assert game.current_player is Player.WHITE
    assert game.scores() == {Player.BLACK: 4, Player.WHITE: 1}


def test_pass_turn_when_current_player_has_no_moves() -> None:
    game = ReversiGame(4)
    game.load_board(
        [
            "BBBB",
            "BBBB",
            "BBBB",
            "BBW.",
        ]
    )
    game.current_player = Player.WHITE

    outcome = game.pass_turn()

    assert outcome is not None
    assert outcome.skipped_player is Player.WHITE
    assert game.current_player is Player.BLACK
    assert not game.game_over


def test_winner_and_payload_roundtrip() -> None:
    game = ReversiGame(4)
    game.load_board(
        [
            "BBBB",
            "BBBB",
            "BBBW",
            "BBBB",
        ]
    )
    game.current_player = Player.WHITE
    game.game_over = True

    payload = game.to_payload()
    restored = ReversiGame.from_payload(payload)

    assert restored.serialize_board() == game.serialize_board()
    assert restored.current_player is Player.WHITE
    assert restored.game_over is True
    assert restored.winner() is Player.BLACK


def test_apply_move_returns_none_for_invalid_cell() -> None:
    game = ReversiGame(8)

    assert game.apply_move(0, 0) is None


def test_board_helpers_and_invalid_payload_shape() -> None:
    game = ReversiGame(4)

    assert game.in_bounds(0, 0) is True
    assert game.in_bounds(-1, 0) is False
    assert game.board_full() is False
    assert game.can_play(Player.BLACK) is True

    with pytest.raises(ValueError):
        game.load_board(["BBBB"])

