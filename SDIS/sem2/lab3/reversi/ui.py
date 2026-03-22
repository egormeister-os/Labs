from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pygame

from reversi.audio import SoundManager
from reversi.config import AppConfig, ThemeConfig, load_app_config, load_help_text
from reversi.controller import GameMode, ReversiController, ScreenState
from reversi.leaderboard import Leaderboard
from reversi.model import MoveOutcome, Player


_FONT_AVAILABLE: bool | None = None


@dataclass(frozen=True)
class Button:
    label: str
    rect: pygame.Rect
    action: str

    def contains(self, position: tuple[int, int]) -> bool:
        return self.rect.collidepoint(position)


def wrap_text(text: str, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines():
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for word in paragraph.split():
            candidate = word if not current else f"{current} {word}"
            if len(candidate) <= width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


def oriented_position(size: int, row: int, col: int, orientation: Player) -> tuple[int, int]:
    if orientation is Player.WHITE:
        last = size - 1
        return last - row, last - col
    return row, col


def render_text(text: str, size: int, color: tuple[int, int, int], *, bold: bool = False) -> pygame.Surface:
    global _FONT_AVAILABLE
    if _FONT_AVAILABLE is not False:
        try:
            font = pygame.font.SysFont("arial", size, bold=bold)
            _FONT_AVAILABLE = True
            return font.render(text, True, color)
        except Exception:
            _FONT_AVAILABLE = False

    width = max(size // 2, len(text) * max(5, size // 3))
    height = max(size + 4, 18)
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    step = max(4, size // 4)
    x = 0
    for char in text:
        if char != " ":
            pygame.draw.rect(surface, color, (x, height // 4, max(3, step - 1), height // 2))
        x += step
        if x >= width - step:
            break
    return surface


class PygameReversiApp:
    def __init__(self, base_dir: Path | str) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.config = load_app_config(self.base_dir)
        help_text = load_help_text(self.config.help_path)
        leaderboard = Leaderboard(self.config.leaderboard_path, self.config.leaderboard_size)
        self.controller = ReversiController(self.config, leaderboard, help_text)
        self.sound_manager = SoundManager(self.config.audio)
        self.screen: pygame.Surface | None = None
        self.clock: pygame.time.Clock | None = None
        self.buttons: list[Button] = []
        self.input_text = ""
        self.pending_animation: MoveOutcome | None = None
        self.animation_started_at = 0

    def setup(self) -> None:
        os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
        pygame.init()
        pygame.display.set_caption("Reversi Laboratory")
        self.screen = pygame.display.set_mode((self.config.window_width, self.config.window_height))
        self.clock = pygame.time.Clock()
        self.sound_manager.initialize()
        self.sound_manager.play_music()

    def run(self) -> None:  # pragma: no cover
        self.setup()
        running = True
        while running:
            now_ms = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_event(event, now_ms)
            outcome = self.controller.update(now_ms)
            if outcome:
                self._register_animation(outcome, now_ms)
            self.draw(now_ms)
            if self.clock:
                self.clock.tick(self.config.fps)
        self.sound_manager.stop_music()
        pygame.quit()

    def handle_event(self, event: pygame.event.Event, now_ms: int) -> None:
        if event.type == pygame.KEYDOWN and self.controller.prompt.active:
            if event.key == pygame.K_RETURN:
                self._submit_prompt()
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.unicode and event.unicode.isprintable():
                self.input_text += event.unicode
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.controller.open_menu()
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.contains(event.pos):
                    self._handle_action(button.action)
                    return

            if self.controller.screen is ScreenState.GAME:
                coords = self._board_position_from_mouse(event.pos)
                if coords is not None:
                    outcome = self.controller.handle_board_move(*coords, now_ms)
                    if outcome:
                        self._register_animation(outcome, now_ms)
                        self.sound_manager.play_sound("move")
                        if outcome.flipped:
                            self.sound_manager.play_sound("flip")

    def _submit_prompt(self) -> None:
        if self.controller.prompt.purpose == "save_name":
            if self.controller.submit_name(self.input_text.strip()):
                self.input_text = ""
        elif self.controller.prompt.purpose == "join_address":
            self.controller.connect_to_host(self.input_text.strip() or self.controller.prompt.placeholder)
            self.input_text = ""

    def _handle_action(self, action: str) -> None:
        if action == "start":
            self.controller.open_mode_select()
        elif action == "records":
            self.controller.open_records()
        elif action == "help":
            self.controller.open_help()
        elif action == "exit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        elif action == "back":
            self.controller.open_menu()
        elif action.startswith("mode:"):
            mode = GameMode(action.split(":", 1)[1])
            self.controller.start_mode(mode)
            if self.controller.prompt.active and self.controller.prompt.purpose == "join_address":
                self.input_text = self.controller.prompt.placeholder

    def _register_animation(self, outcome: MoveOutcome, now_ms: int) -> None:
        self.pending_animation = outcome
        self.animation_started_at = now_ms
        if outcome.game_over:
            self.sound_manager.play_sound("win")

    def draw(self, now_ms: int) -> None:
        if self.screen is None:
            return
        theme = self.config.theme
        self.screen.fill(theme.background_color)
        self.buttons = []

        if self.controller.screen is ScreenState.MENU:
            self._draw_menu(theme)
        elif self.controller.screen is ScreenState.MODE_SELECT:
            self._draw_mode_select(theme)
        elif self.controller.screen is ScreenState.HELP:
            self._draw_help(theme)
        elif self.controller.screen is ScreenState.RECORDS:
            self._draw_records(theme)
        elif self.controller.screen is ScreenState.WAITING:
            self._draw_waiting(theme)
        elif self.controller.screen is ScreenState.GAME:
            self._draw_game(theme, now_ms)

        if self.controller.prompt.active:
            self._draw_prompt(theme)
        pygame.display.flip()

    def _draw_menu(self, theme: ThemeConfig) -> None:
        actions = [
            ("Начать игру", "start"),
            ("Таблица рекордов", "records"),
            ("Справка", "help"),
            ("Выход", "exit"),
        ]
        self._draw_title("Reversi")
        self._draw_status()
        self.buttons = self._build_buttons(actions)
        self._draw_buttons(theme)

    def _draw_mode_select(self, theme: ThemeConfig) -> None:
        actions = [
            ("С компьютером", f"mode:{GameMode.VS_AI.value}"),
            ("Тренировка", f"mode:{GameMode.PRACTICE.value}"),
            ("Два игрока", f"mode:{GameMode.LOCAL_TWO.value}"),
            ("Онлайн: host", f"mode:{GameMode.ONLINE_HOST.value}"),
            ("Онлайн: join", f"mode:{GameMode.ONLINE_JOIN.value}"),
            ("Назад", "back"),
        ]
        self._draw_title("Выбор режима")
        self._draw_status()
        self.buttons = self._build_buttons(actions, top=140, height=58)
        self._draw_buttons(theme)

    def _draw_help(self, theme: ThemeConfig) -> None:
        self._draw_title("Справка")
        self._draw_status()
        top = 130
        for line in wrap_text(self.controller.help_text, 70):
            rendered = render_text(line, 22, theme.text_color)
            self.screen.blit(rendered, (60, top))
            top += 28
        self.buttons = self._build_buttons([("Назад", "back")], top=self.config.window_height - 110)
        self._draw_buttons(theme)

    def _draw_records(self, theme: ThemeConfig) -> None:
        self._draw_title("Таблица рекордов")
        self._draw_status()
        top = 140
        if not self.controller.leaderboard.entries:
            empty = render_text("Рекордов пока нет.", 24, theme.text_color)
            self.screen.blit(empty, (80, top))
        else:
            for index, entry in enumerate(self.controller.leaderboard.entries, start=1):
                line = f"{index:>2}. {entry.name:<12} {entry.score:>2}  {entry.mode}  {entry.played_at}"
                rendered = render_text(line, 24, theme.text_color)
                self.screen.blit(rendered, (60, top))
                top += 34
        self.buttons = self._build_buttons([("Назад", "back")], top=self.config.window_height - 110)
        self._draw_buttons(theme)

    def _draw_waiting(self, theme: ThemeConfig) -> None:
        self._draw_title("Онлайн-режим")
        self._draw_status()
        self.buttons = self._build_buttons([("Назад", "back")], top=self.config.window_height - 110)
        self._draw_buttons(theme)

    def _draw_game(self, theme: ThemeConfig, now_ms: int) -> None:
        if not self.controller.game or self.screen is None:
            return

        board_rect = pygame.Rect(40, 120, 640, 640)
        side_rect = pygame.Rect(720, 120, 420, 640)
        pygame.draw.rect(self.screen, theme.panel_color, side_rect, border_radius=14)
        self._draw_title("Reversi")
        self._draw_status()
        self._draw_board(board_rect, theme, now_ms)
        self._draw_sidebar(side_rect, theme)
        self.buttons = self._build_buttons([("Назад в меню", "back")], left=760, top=680, width=320)
        self._draw_buttons(theme)

    def _draw_board(self, rect: pygame.Rect, theme: ThemeConfig, now_ms: int) -> None:
        assert self.controller.game is not None
        game = self.controller.game
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        surface.fill(theme.board_color)
        cell_size = rect.width // game.size

        for index in range(game.size + 1):
            offset = index * cell_size
            pygame.draw.line(surface, theme.grid_color, (offset, 0), (offset, rect.height), 2)
            pygame.draw.line(surface, theme.grid_color, (0, offset), (rect.width, offset), 2)

        legal_moves = set(game.legal_moves().keys()) if self.controller.is_local_turn() else set()
        orientation = self.controller.current_orientation()
        animation_factor = min(1.0, (now_ms - self.animation_started_at) / max(1, self.config.animation_ms))

        for row in range(game.size):
            for col in range(game.size):
                draw_row, draw_col = oriented_position(game.size, row, col, orientation)
                cell_rect = pygame.Rect(draw_col * cell_size, draw_row * cell_size, cell_size, cell_size)
                cell_value = game.board[row][col]
                if cell_value is None:
                    if (row, col) in legal_moves:
                        pygame.draw.circle(surface, theme.hint_color, cell_rect.center, cell_size // 8)
                    continue

                disc_color = theme.black_disc_color if cell_value is Player.BLACK else theme.white_disc_color
                radius = int(cell_size * 0.38)
                if self.pending_animation and (row, col) in self.pending_animation.flipped:
                    radius = int(radius * (0.55 + 0.45 * animation_factor))
                pygame.draw.circle(surface, disc_color, cell_rect.center, radius)

        self.screen.blit(surface, rect)

    def _draw_sidebar(self, rect: pygame.Rect, theme: ThemeConfig) -> None:
        assert self.controller.game is not None
        game = self.controller.game
        scores = game.scores()
        orientation = self.controller.current_orientation().value.lower()
        lines = [
            f"Черные: {scores[Player.BLACK]}",
            f"Белые: {scores[Player.WHITE]}",
            f"Ход: {game.current_player.value.lower()}",
            f"Ориентация: {orientation}",
            "",
            "Режимы:",
            "С компьютером",
            "Тренировка",
            "Локально на двоих",
            "Онлайн host/join",
        ]
        top = rect.top + 40
        for index, line in enumerate(lines):
            text = render_text(line, 28 if index < 4 else 24, theme.text_color)
            self.screen.blit(text, (rect.left + 28, top))
            top += 42 if index < 4 else 32

    def _draw_prompt(self, theme: ThemeConfig) -> None:
        panel = pygame.Rect(250, 260, 680, 220)
        pygame.draw.rect(self.screen, theme.panel_color, panel, border_radius=20)
        pygame.draw.rect(self.screen, theme.accent_color, panel, width=3, border_radius=20)
        title = render_text(self.controller.prompt.title, 34, theme.text_color)
        self.screen.blit(title, (panel.left + 30, panel.top + 25))
        value = self.input_text or self.controller.prompt.placeholder
        rendered = render_text(value, 30, theme.text_color)
        self.screen.blit(rendered, (panel.left + 30, panel.top + 110))
        note = render_text("Enter - подтвердить, Backspace - удалить", 30, theme.warning_color)
        self.screen.blit(note, (panel.left + 30, panel.top + 160))

    def _draw_title(self, title: str) -> None:
        rendered = render_text(title, 56, self.config.theme.accent_color, bold=True)
        self.screen.blit(rendered, (40, 32))

    def _draw_status(self) -> None:
        rendered = render_text(self.controller.status_message, 24, self.config.theme.text_color)
        self.screen.blit(rendered, (42, 92))

    def _build_buttons(
        self,
        definitions: list[tuple[str, str]],
        *,
        left: int = 60,
        top: int = 180,
        width: int = 380,
        height: int = 64,
    ) -> list[Button]:
        buttons = []
        gap = 18
        for index, (label, action) in enumerate(definitions):
            rect = pygame.Rect(left, top + index * (height + gap), width, height)
            buttons.append(Button(label=label, rect=rect, action=action))
        return buttons

    def _draw_buttons(self, theme: ThemeConfig) -> None:
        for button in self.buttons:
            pygame.draw.rect(self.screen, theme.panel_color, button.rect, border_radius=14)
            pygame.draw.rect(self.screen, theme.accent_color, button.rect, width=2, border_radius=14)
            rendered = render_text(button.label, 30, theme.text_color)
            self.screen.blit(rendered, (button.rect.x + 20, button.rect.y + 18))

    def _board_position_from_mouse(self, position: tuple[int, int]) -> tuple[int, int] | None:
        if not self.controller.game:
            return None
        board_rect = pygame.Rect(40, 120, 640, 640)
        if not board_rect.collidepoint(position):
            return None
        cell_size = board_rect.width // self.controller.game.size
        col = (position[0] - board_rect.left) // cell_size
        row = (position[1] - board_rect.top) // cell_size
        return row, col


def run_app(base_dir: Path | str) -> None:  # pragma: no cover
    app = PygameReversiApp(base_dir)
    app.run()
