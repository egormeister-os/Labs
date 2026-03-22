from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from reversi.ai import GreedyAI
from reversi.config import AppConfig
from reversi.leaderboard import Leaderboard
from reversi.model import MoveOutcome, Player, ReversiGame
from reversi.network import OnlineClient, OnlineServer


class ScreenState(str, Enum):
    MENU = "menu"
    MODE_SELECT = "mode_select"
    HELP = "help"
    RECORDS = "records"
    WAITING = "waiting"
    GAME = "game"


class GameMode(str, Enum):
    PRACTICE = "practice"
    VS_AI = "vs_ai"
    LOCAL_TWO = "local_two"
    ONLINE_HOST = "online_host"
    ONLINE_JOIN = "online_join"


@dataclass
class PromptState:
    active: bool = False
    title: str = ""
    placeholder: str = ""
    purpose: str = ""


class ReversiController:
    def __init__(self, config: AppConfig, leaderboard: Leaderboard, help_text: str) -> None:
        self.config = config
        self.help_text = help_text
        self.leaderboard = leaderboard
        self.ai = GreedyAI()

        self.screen = ScreenState.MENU
        self.game: ReversiGame | None = None
        self.mode: GameMode | None = None
        self.status_message = "Выберите пункт меню."
        self.prompt = PromptState()
        self.awaiting_name_score: int | None = None
        self.awaiting_name_mode: str = ""
        self.local_player = Player.BLACK
        self.ai_player = Player.WHITE
        self.server: OnlineServer | None = None
        self.client: OnlineClient | None = None
        self.ai_ready_at = 0

    def open_menu(self) -> None:
        self.screen = ScreenState.MENU
        self.prompt = PromptState()
        self.status_message = "Выберите пункт меню."
        self._close_network()

    def open_help(self) -> None:
        self.screen = ScreenState.HELP
        self.status_message = "Справка по правилам Reversi."

    def open_records(self) -> None:
        self.screen = ScreenState.RECORDS
        self.leaderboard.load()
        self.status_message = "Таблица рекордов."

    def open_mode_select(self) -> None:
        self.screen = ScreenState.MODE_SELECT
        self.status_message = "Выберите режим игры."

    def start_mode(self, mode: GameMode) -> None:
        self._close_network()
        self.mode = mode
        self.game = ReversiGame(self.config.board_size)
        self.local_player = Player.BLACK
        self.screen = ScreenState.GAME
        self.prompt = PromptState()

        if mode is GameMode.VS_AI:
            self.status_message = "Режим против компьютера. Вы играете черными."
        elif mode is GameMode.PRACTICE:
            self.status_message = "Тренировочный режим."
        elif mode is GameMode.LOCAL_TWO:
            self.status_message = "Локальная игра на двоих. Доска будет поворачиваться."
        elif mode is GameMode.ONLINE_HOST:
            self.server = OnlineServer(
                self.config.network.host,
                self.config.network.port,
                self.config.network.backlog,
            )
            self.server.start()
            self.screen = ScreenState.WAITING
            self.status_message = (
                f"Ожидание игрока на {self.config.network.host}:{self.config.network.port}."
            )
        elif mode is GameMode.ONLINE_JOIN:
            self.screen = ScreenState.MODE_SELECT
            self.prompt = PromptState(
                active=True,
                title="Подключение к игре",
                placeholder=f"{self.config.network.host}:{self.config.network.port}",
                purpose="join_address",
            )
            self.status_message = "Введите адрес сервера в формате host:port."

    def connect_to_host(self, value: str) -> None:
        host, _, port_raw = value.partition(":")
        port = int(port_raw or self.config.network.port)
        self.client = OnlineClient(host or self.config.network.host, port, self.config.network.connect_timeout)
        self.client.connect()
        self.mode = GameMode.ONLINE_JOIN
        self.game = ReversiGame(self.config.board_size)
        self.local_player = Player.WHITE
        self.prompt = PromptState()
        self.screen = ScreenState.WAITING
        self.status_message = f"Подключено к {host or self.config.network.host}:{port}. Ожидание состояния игры."

    def submit_name(self, name: str) -> bool:
        if self.awaiting_name_score is None:
            return False
        self.leaderboard.add_entry(name, self.awaiting_name_score, self.awaiting_name_mode)
        self.awaiting_name_score = None
        self.awaiting_name_mode = ""
        self.prompt = PromptState()
        self.status_message = "Результат сохранен в таблицу рекордов."
        return True

    def current_orientation(self) -> Player:
        if self.mode in {GameMode.LOCAL_TWO, GameMode.ONLINE_HOST, GameMode.ONLINE_JOIN} and self.game:
            return self.game.current_player
        return Player.BLACK

    def is_local_turn(self) -> bool:
        if not self.game or self.mode is None:
            return False
        if self.mode in {GameMode.PRACTICE, GameMode.LOCAL_TWO}:
            return True
        if self.mode is GameMode.VS_AI:
            return self.game.current_player is self.local_player
        if self.mode is GameMode.ONLINE_HOST:
            return self.game.current_player is Player.BLACK
        if self.mode is GameMode.ONLINE_JOIN:
            return self.game.current_player is self.local_player
        return False

    def board_coords_from_display(self, row: int, col: int) -> tuple[int, int]:
        if not self.game:
            return row, col
        if self.current_orientation() is Player.WHITE:
            last = self.game.size - 1
            return last - row, last - col
        return row, col

    def display_coords_from_board(self, row: int, col: int) -> tuple[int, int]:
        return self.board_coords_from_display(row, col)

    def handle_board_move(self, row: int, col: int, now_ms: int) -> MoveOutcome | None:
        if not self.game or not self.is_local_turn():
            return None

        board_row, board_col = self.board_coords_from_display(row, col)
        if self.mode is GameMode.ONLINE_JOIN:
            if not self.client:
                return None
            outcome = self.game.apply_move(board_row, board_col)
            if outcome:
                self.client.send_move(board_row, board_col)
                self._update_after_move(outcome, now_ms)
                return outcome
            return None

        if self.mode is GameMode.ONLINE_HOST:
            outcome = self.game.apply_move(board_row, board_col)
            if outcome and self.server:
                self.server.send_state(self.game)
                self._update_after_move(outcome, now_ms)
            return outcome

        outcome = self.game.apply_move(board_row, board_col)
        if outcome:
            self._update_after_move(outcome, now_ms)
        return outcome

    def update(self, now_ms: int) -> MoveOutcome | None:
        if not self.game or self.mode is None:
            return None

        if self.mode is GameMode.ONLINE_HOST and self.server:
            if self.screen is ScreenState.WAITING and self.server.accept_client():
                self.screen = ScreenState.GAME
                self.status_message = "Игрок подключился. Ход черных."
                self.server.send_state(self.game)
            elif self.screen is ScreenState.GAME and self.server.poll_client(self.game):
                self.status_message = f"Ход {self.game.current_player.value.lower()}."
                self._check_completion()

        if self.mode is GameMode.ONLINE_JOIN and self.client and self.client.poll_messages(self.game):
            self.screen = ScreenState.GAME
            self.status_message = f"Состояние игры обновлено. Ход {self.game.current_player.value.lower()}."
            self._check_completion()

        if self.game.game_over:
            self._check_completion()
            return None

        if not self.game.can_play(self.game.current_player):
            outcome = self.game.pass_turn()
            if outcome:
                self.status_message = "Ход пропущен: у текущего игрока нет допустимых ходов."
                if self.mode is GameMode.ONLINE_HOST and self.server:
                    self.server.send_state(self.game)
                self._check_completion()
                return outcome

        if self.mode is GameMode.VS_AI and self.game.current_player is self.ai_player and now_ms >= self.ai_ready_at:
            move = self.ai.choose_move(self.game, self.ai_player)
            if move is not None:
                outcome = self.game.apply_move(*move)
                if outcome:
                    self._update_after_move(outcome, now_ms)
                    return outcome
        return None

    def _update_after_move(self, outcome: MoveOutcome, now_ms: int) -> None:
        if outcome.skipped_player:
            self.status_message = "Ход соперника пропущен: допустимых ходов нет."
        else:
            self.status_message = f"Следующий ход: {outcome.next_player.value.lower()}."

        if self.mode is GameMode.VS_AI and self.game and self.game.current_player is self.ai_player:
            self.ai_ready_at = now_ms + self.config.ai_delay_ms
        self._check_completion()

    def _check_completion(self) -> None:
        if not self.game or not self.game.game_over:
            return
        winner = self.game.winner()
        scores = self.game.scores()
        if winner is None:
            self.status_message = "Игра окончена. Ничья."
            return

        winner_score = scores[winner]
        self.status_message = f"Победил {winner.value.lower()} со счетом {winner_score}."
        if self._winner_is_local(winner) and self.leaderboard.is_new_record(winner_score):
            self.awaiting_name_score = winner_score
            self.awaiting_name_mode = self.mode.value if self.mode else "unknown"
            self.prompt = PromptState(
                active=True,
                title="Новый рекорд",
                placeholder="Введите имя",
                purpose="save_name",
            )

    def _winner_is_local(self, winner: Player) -> bool:
        if self.mode in {GameMode.PRACTICE, GameMode.LOCAL_TWO}:
            return True
        if self.mode is GameMode.VS_AI:
            return winner is self.local_player
        return winner is self.local_player

    def _close_network(self) -> None:
        if self.server:
            self.server.close()
            self.server = None
        if self.client:
            self.client.close()
            self.client = None
