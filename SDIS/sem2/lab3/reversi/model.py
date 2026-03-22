from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


Position = tuple[int, int]
Board = list[list["Player | None"]]


class Player(str, Enum):
    BLACK = "BLACK"
    WHITE = "WHITE"

    def other(self) -> "Player":
        return Player.WHITE if self is Player.BLACK else Player.BLACK

    def to_symbol(self) -> str:
        return "B" if self is Player.BLACK else "W"

    @classmethod
    def from_symbol(cls, symbol: str) -> "Player | None":
        if symbol == "B":
            return cls.BLACK
        if symbol == "W":
            return cls.WHITE
        return None


@dataclass(frozen=True)
class MoveOutcome:
    player: Player
    position: Position | None
    flipped: list[Position] = field(default_factory=list)
    next_player: Player | None = None
    skipped_player: Player | None = None
    game_over: bool = False


class ReversiGame:
    DIRECTIONS: tuple[Position, ...] = (
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, -1),
        (0, 1),
        (1, -1),
        (1, 0),
        (1, 1),
    )

    def __init__(self, size: int = 8) -> None:
        if size < 4 or size % 2 != 0:
            raise ValueError("Board size must be an even number >= 4")
        self.size = size
        self.board: Board = []
        self.current_player = Player.BLACK
        self.game_over = False
        self.reset()

    def reset(self) -> None:
        self.board = [[None for _ in range(self.size)] for _ in range(self.size)]
        center = self.size // 2
        self.board[center - 1][center - 1] = Player.WHITE
        self.board[center][center] = Player.WHITE
        self.board[center - 1][center] = Player.BLACK
        self.board[center][center - 1] = Player.BLACK
        self.current_player = Player.BLACK
        self.game_over = False

    def copy_board(self) -> Board:
        return [row[:] for row in self.board]

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size

    def scores(self) -> dict[Player, int]:
        black = sum(cell is Player.BLACK for row in self.board for cell in row)
        white = sum(cell is Player.WHITE for row in self.board for cell in row)
        return {Player.BLACK: black, Player.WHITE: white}

    def score_for(self, player: Player) -> int:
        return self.scores()[player]

    def board_full(self) -> bool:
        return all(cell is not None for row in self.board for cell in row)

    def _captures_for_direction(
        self,
        row: int,
        col: int,
        player: Player,
        direction: Position,
    ) -> list[Position]:
        delta_row, delta_col = direction
        current_row = row + delta_row
        current_col = col + delta_col
        captured: list[Position] = []

        while self.in_bounds(current_row, current_col):
            cell = self.board[current_row][current_col]
            if cell is None:
                return []
            if cell is player:
                return captured if captured else []
            captured.append((current_row, current_col))
            current_row += delta_row
            current_col += delta_col
        return []

    def legal_moves(self, player: Player | None = None) -> dict[Position, list[Position]]:
        player = player or self.current_player
        moves: dict[Position, list[Position]] = {}
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] is not None:
                    continue
                flips: list[Position] = []
                for direction in self.DIRECTIONS:
                    flips.extend(self._captures_for_direction(row, col, player, direction))
                if flips:
                    moves[(row, col)] = flips
        return moves

    def can_play(self, player: Player | None = None) -> bool:
        return bool(self.legal_moves(player))

    def apply_move(self, row: int, col: int) -> MoveOutcome | None:
        if self.game_over:
            return None

        moves = self.legal_moves(self.current_player)
        flips = moves.get((row, col))
        if not flips:
            return None

        player = self.current_player
        self.board[row][col] = player
        for flip_row, flip_col in flips:
            self.board[flip_row][flip_col] = player

        next_player = player.other()
        skipped_player: Player | None = None
        if self.board_full():
            self.game_over = True
        elif not self.can_play(next_player):
            if self.can_play(player):
                skipped_player = next_player
                next_player = player
            else:
                self.game_over = True

        self.current_player = next_player
        return MoveOutcome(
            player=player,
            position=(row, col),
            flipped=flips,
            next_player=next_player,
            skipped_player=skipped_player,
            game_over=self.game_over,
        )

    def pass_turn(self) -> MoveOutcome | None:
        if self.game_over or self.can_play(self.current_player):
            return None

        skipped_player = self.current_player
        next_player = self.current_player.other()
        if self.can_play(next_player):
            self.current_player = next_player
            return MoveOutcome(
                player=next_player,
                position=None,
                flipped=[],
                next_player=next_player,
                skipped_player=skipped_player,
                game_over=False,
            )

        self.game_over = True
        return MoveOutcome(
            player=skipped_player,
            position=None,
            flipped=[],
            next_player=next_player,
            skipped_player=skipped_player,
            game_over=True,
        )

    def winner(self) -> Player | None:
        scores = self.scores()
        if scores[Player.BLACK] > scores[Player.WHITE]:
            return Player.BLACK
        if scores[Player.WHITE] > scores[Player.BLACK]:
            return Player.WHITE
        return None

    def serialize_board(self) -> list[str]:
        rows: list[str] = []
        for row in self.board:
            rows.append("".join(cell.to_symbol() if cell else "." for cell in row))
        return rows

    def load_board(self, rows: Iterable[str]) -> None:
        board_rows = list(rows)
        if len(board_rows) != self.size:
            raise ValueError("Serialized board has incorrect row count")
        new_board: Board = []
        for row in board_rows:
            if len(row) != self.size:
                raise ValueError("Serialized board has incorrect column count")
            new_board.append([Player.from_symbol(symbol) for symbol in row])
        self.board = new_board

    def to_payload(self) -> dict:
        return {
            "size": self.size,
            "board": self.serialize_board(),
            "current_player": self.current_player.value,
            "game_over": self.game_over,
        }

    @classmethod
    def from_payload(cls, payload: dict) -> "ReversiGame":
        game = cls(size=int(payload["size"]))
        game.load_board(payload["board"])
        game.current_player = Player(payload["current_player"])
        game.game_over = bool(payload["game_over"])
        return game

