from __future__ import annotations

from reversi.model import Player, Position, ReversiGame


class GreedyAI:
    def choose_move(self, game: ReversiGame, player: Player | None = None) -> Position | None:
        player = player or game.current_player
        moves = game.legal_moves(player)
        if not moves:
            return None

        best_score: int | None = None
        best_move: Position | None = None
        for move, flips in moves.items():
            score = self._score_move(game, move, flips)
            if best_score is None or score > best_score:
                best_score = score
                best_move = move
        return best_move

    def _score_move(self, game: ReversiGame, move: Position, flips: list[Position]) -> int:
        row, col = move
        last_index = game.size - 1
        corners = {(0, 0), (0, last_index), (last_index, 0), (last_index, last_index)}

        score = len(flips) * 10
        if move in corners:
            score += 1000
        elif row in (0, last_index) or col in (0, last_index):
            score += 100

        center_distance = abs(row - last_index / 2) + abs(col - last_index / 2)
        score -= int(center_distance)
        return score

