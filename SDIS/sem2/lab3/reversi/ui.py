from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pygame

from reversi.audio import SoundManager
from reversi.config import ThemeConfig, load_app_config, load_help_text
from reversi.controller import GameMode, ReversiController, ScreenState
from reversi.leaderboard import Leaderboard
from reversi.model import MoveOutcome, Player


_FONT_AVAILABLE: bool | None = None
_FONT_FILE: Path | None = None
_FONT_CACHE: dict[tuple[int, bool], object] = {}


@dataclass(frozen=True)
class Button:
    label: str
    rect: pygame.Rect
    action: str
    subtitle: str = ""
    primary: bool = False

    def contains(self, position: tuple[int, int]) -> bool:
        return self.rect.collidepoint(position)


@dataclass(frozen=True)
class GameLayout:
    header: pygame.Rect
    board_frame: pygame.Rect
    board: pygame.Rect
    sidebar: pygame.Rect


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


def wrap_text_to_width(text: str, size: int, max_width: int, *, bold: bool = False) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines():
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for word in paragraph.split():
            candidate = word if not current else f"{current} {word}"
            if not current:
                current = candidate
                continue
            if render_text(candidate, size, (255, 255, 255), bold=bold).get_width() <= max_width:
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


def mix_color(left: tuple[int, int, int], right: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(
        int(left[index] + (right[index] - left[index]) * amount)
        for index in range(3)
    )


def alpha_color(color: tuple[int, int, int], alpha: int) -> tuple[int, int, int, int]:
    return color[0], color[1], color[2], alpha


def inflate(rect: pygame.Rect, x: int, y: int) -> pygame.Rect:
    return pygame.Rect(rect.x - x, rect.y - y, rect.width + x * 2, rect.height + y * 2)


def _find_font_file() -> Path | None:
    global _FONT_FILE
    if _FONT_FILE is not None:
        return _FONT_FILE

    candidates = [
        Path("/usr/share/fonts/gnu-free/FreeSans.otf"),
        Path("/usr/share/fonts/gnu-free/FreeSerif.otf"),
        Path("/usr/share/fonts/gsfonts/NimbusSans-Regular.otf"),
        Path("/usr/share/fonts/gsfonts/NimbusSansNarrow-Regular.otf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            _FONT_FILE = candidate
            return _FONT_FILE
    return None


def _load_freetype_font(size: int, bold: bool) -> object | None:
    key = (size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]

    font_path = _find_font_file()
    if font_path is None:
        return None

    try:
        import pygame._freetype as freetype

        if not freetype.get_init():
            freetype.init()
        font = freetype.Font(str(font_path), size)
        font.strong = bold
        _FONT_CACHE[key] = font
        return font
    except Exception:
        return None


def render_text(text: str, size: int, color: tuple[int, int, int], *, bold: bool = False) -> pygame.Surface:
    global _FONT_AVAILABLE
    if _FONT_AVAILABLE is not False:
        try:
            freetype_font = _load_freetype_font(size, bold)
            if freetype_font is not None:
                _FONT_AVAILABLE = True
                surface, _ = freetype_font.render(text, color)
                return surface

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


def blit_text_block(
    surface: pygame.Surface,
    text: str,
    x_pos: int,
    y_pos: int,
    max_width: int,
    size: int,
    color: tuple[int, int, int],
    *,
    bold: bool = False,
    line_height: int | None = None,
    max_lines: int | None = None,
) -> int:
    lines = wrap_text_to_width(text, size, max_width, bold=bold)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            last = lines[-1].rstrip(". ")
            lines[-1] = f"{last}..."
    current_y = y_pos
    step = line_height or size + 6
    for line in lines:
        rendered = render_text(line, size, color, bold=bold)
        surface.blit(rendered, (x_pos, current_y))
        current_y += step if line else max(10, step // 2)
    return current_y


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
        self.active_action = ""
        self.active_action_until = 0

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
            self.sound_manager.pump()
            self.draw(now_ms)
            if self.clock:
                self.clock.tick(self.config.fps)
        self.sound_manager.shutdown()
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
                    self.active_action = button.action
                    self.active_action_until = now_ms + 180
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
                    elif self.controller.is_local_turn():
                        self.sound_manager.play_sound("error")

    def _submit_prompt(self) -> None:
        if self.controller.prompt.purpose == "save_name":
            if self.controller.submit_name(self.input_text.strip()):
                self.input_text = ""
        elif self.controller.prompt.purpose == "join_address":
            try:
                self.controller.connect_to_host(self.input_text.strip() or self.controller.prompt.placeholder)
                self.input_text = ""
            except OSError:
                self.controller.status_message = "Не удалось подключиться к серверу."
                self.sound_manager.play_sound("error")

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
        self.buttons = []
        self._draw_background(theme, now_ms)

        if self.controller.screen is ScreenState.MENU:
            self._draw_menu(theme, now_ms)
        elif self.controller.screen is ScreenState.MODE_SELECT:
            self._draw_mode_select(theme, now_ms)
        elif self.controller.screen is ScreenState.HELP:
            self._draw_help(theme, now_ms)
        elif self.controller.screen is ScreenState.RECORDS:
            self._draw_records(theme, now_ms)
        elif self.controller.screen is ScreenState.WAITING:
            self._draw_waiting(theme, now_ms)
        elif self.controller.screen is ScreenState.GAME:
            self._draw_game(theme, now_ms)

        if self.controller.prompt.active:
            self._draw_prompt(theme)
        pygame.display.flip()

    def _draw_background(self, theme: ThemeConfig, now_ms: int) -> None:
        assert self.screen is not None
        surface = self.screen
        rect = surface.get_rect()
        top_color = mix_color(theme.background_color, theme.panel_color, 0.15)
        bottom_color = mix_color(theme.background_color, (3, 9, 9), 0.45)

        for offset in range(rect.height):
            factor = offset / max(1, rect.height - 1)
            color = mix_color(top_color, bottom_color, factor)
            pygame.draw.line(surface, color, (0, offset), (rect.width, offset))

        glow = pygame.Surface(rect.size, pygame.SRCALPHA)
        accent = theme.accent_color
        circles = [
            ((160, 90), 180, 24),
            ((980, 120), 160, 18),
            ((1020, 700), 220, 16),
            ((210, 660), 260, 12),
        ]
        for index, (center, radius, alpha) in enumerate(circles):
            phase = (now_ms // 40 + index * 7) % 30
            pygame.draw.circle(glow, alpha_color(accent, alpha + phase), center, radius)
        surface.blit(glow, (0, 0))

        for x_offset in range(0, rect.width, 44):
            color = alpha_color(mix_color(theme.accent_color, theme.background_color, 0.75), 18)
            pygame.draw.line(surface, color, (x_offset, 0), (x_offset - 90, rect.height), 1)

    def _draw_menu(self, theme: ThemeConfig, now_ms: int) -> None:
        assert self.screen is not None
        hero = pygame.Rect(70, 48, 1040, 680)
        self._draw_panel(hero, theme, glass=True, shadow=True)
        self._draw_disc_pattern(hero, theme)

        title = render_text("Reversi", 80, theme.accent_color, bold=True)
        subtitle = render_text("Классическая стратегия с локальным и онлайн-режимами", 27, theme.text_color)
        status = render_text(self.controller.status_message, 23, mix_color(theme.text_color, theme.accent_color, 0.25))
        self.screen.blit(title, (hero.x + 70, hero.y + 48))
        self.screen.blit(subtitle, (hero.x + 72, hero.y + 140))
        self.screen.blit(status, (hero.x + 72, hero.y + 188))

        actions = [
            ("Начать игру", "start", "Матч против ИИ, локально или онлайн", True),
            ("Таблица рекордов", "records", "Лучшие результаты игроков", False),
            ("Справка", "help", "Правила и подсказки по режимам", False),
            ("Выход", "exit", "Закрыть приложение", False),
        ]
        self.buttons = self._build_buttons(actions, left=hero.x + 72, top=hero.y + 270, width=410, height=82, gap=20)
        self._draw_buttons(theme, now_ms)

        info_rect = pygame.Rect(hero.right - 380, hero.y + 260, 300, 290)
        self._draw_panel(info_rect, theme, accent=True)
        self._draw_info_lines(
            info_rect,
            [
                "Режимы",
                "С компьютером",
                "Тренировка",
                "Два игрока",
                "Онлайн host/join",
            ],
            theme,
            title_size=30,
        )

    def _draw_mode_select(self, theme: ThemeConfig, now_ms: int) -> None:
        assert self.screen is not None
        panel = pygame.Rect(70, 48, 1040, 690)
        self._draw_panel(panel, theme, glass=True, shadow=True)
        title = render_text("Выбор режима", 58, theme.accent_color, bold=True)
        subtitle = render_text("Выберите, как хотите провести следующую партию", 24, theme.text_color)
        self.screen.blit(title, (panel.x + 60, panel.y + 44))
        self.screen.blit(subtitle, (panel.x + 62, panel.y + 118))

        actions = [
            ("С компьютером", f"mode:{GameMode.VS_AI.value}", "Стандартный матч против жадного ИИ", True),
            ("Тренировка", f"mode:{GameMode.PRACTICE.value}", "Игра с самим собой для отработки тактики", False),
            ("Два игрока", f"mode:{GameMode.LOCAL_TWO.value}", "Одна доска, один экран, с поворотом после хода", False),
            ("Онлайн: host", f"mode:{GameMode.ONLINE_HOST.value}", "Открыть локальный сервер и ждать соперника", False),
            ("Онлайн: join", f"mode:{GameMode.ONLINE_JOIN.value}", "Подключиться к уже запущенной игре", False),
            ("Назад", "back", "Вернуться в главное меню", False),
        ]

        buttons: list[Button] = []
        button_width = 430
        button_height = 86
        gap_x = 30
        gap_y = 24
        start_x = panel.x + 60
        start_y = panel.y + 190
        for index, (label, action, subtitle_text, primary) in enumerate(actions):
            row = index // 2
            col = index % 2
            rect = pygame.Rect(
                start_x + col * (button_width + gap_x),
                start_y + row * (button_height + gap_y),
                button_width,
                button_height,
            )
            buttons.append(Button(label, rect, action, subtitle_text, primary))
        self.buttons = buttons
        self._draw_buttons(theme, now_ms)

    def _draw_help(self, theme: ThemeConfig, now_ms: int) -> None:
        assert self.screen is not None
        card = pygame.Rect(70, 48, 1040, 690)
        self._draw_panel(card, theme, glass=True, shadow=True)
        title = render_text("Справка", 56, theme.accent_color, bold=True)
        self.screen.blit(title, (card.x + 58, card.y + 42))
        self._draw_tag(card.right - 250, card.y + 46, "Правила игры", theme)

        content = pygame.Rect(card.x + 50, card.y + 120, card.width - 100, 500)
        self._draw_panel(content, theme, inner=True)
        blit_text_block(
            self.screen,
            self._help_body_text(),
            content.x + 28,
            content.y + 22,
            content.width - 56,
            20,
            theme.text_color,
            line_height=26,
        )

        self.buttons = self._build_buttons([("Назад", "back", "", False)], left=card.x + 50, top=card.bottom - 92, width=260, height=62)
        self._draw_buttons(theme, now_ms)

    def _draw_records(self, theme: ThemeConfig, now_ms: int) -> None:
        assert self.screen is not None
        card = pygame.Rect(70, 48, 1040, 690)
        self._draw_panel(card, theme, glass=True, shadow=True)
        title = render_text("Таблица рекордов", 54, theme.accent_color, bold=True)
        self.screen.blit(title, (card.x + 58, card.y + 42))
        self._draw_tag(card.right - 270, card.y + 46, "Лучшие партии", theme)

        table = pygame.Rect(card.x + 50, card.y + 120, card.width - 100, 470)
        self._draw_panel(table, theme, inner=True)

        header = ["#", "Игрок", "Очки", "Режим", "Дата"]
        x_positions = [table.x + 28, table.x + 96, table.x + 380, table.x + 500, table.x + 700]
        for text, x_pos in zip(header, x_positions):
            self.screen.blit(render_text(text, 23, mix_color(theme.text_color, theme.accent_color, 0.35), bold=True), (x_pos, table.y + 24))

        if not self.controller.leaderboard.entries:
            empty = render_text("Рекордов пока нет.", 28, theme.text_color)
            self.screen.blit(empty, (table.x + 30, table.y + 96))
        else:
            top = table.y + 74
            medal_colors = [
                theme.accent_color,
                mix_color(theme.text_color, theme.accent_color, 0.45),
                mix_color(theme.accent_color, theme.panel_color, 0.35),
            ]
            for index, entry in enumerate(self.controller.leaderboard.entries, start=1):
                row_rect = pygame.Rect(table.x + 18, top - 8, table.width - 36, 44)
                pygame.draw.rect(self.screen, mix_color(theme.panel_color, theme.board_color, 0.20), row_rect, border_radius=14)
                if index <= 3:
                    pygame.draw.circle(self.screen, medal_colors[index - 1], (table.x + 42, top + 12), 12)
                row_values = [
                    str(index),
                    entry.name,
                    str(entry.score),
                    entry.mode,
                    entry.played_at,
                ]
                for text, x_pos in zip(row_values, x_positions):
                    self.screen.blit(render_text(text, 23, theme.text_color), (x_pos, top))
                top += 56

        self.buttons = self._build_buttons([("Назад", "back", "", False)], left=card.x + 50, top=card.bottom - 92, width=260, height=62)
        self._draw_buttons(theme, now_ms)

    def _draw_waiting(self, theme: ThemeConfig, now_ms: int) -> None:
        assert self.screen is not None
        card = pygame.Rect(240, 180, 700, 380)
        self._draw_panel(card, theme, glass=True, shadow=True)
        title = render_text("Онлайн-режим", 52, theme.accent_color, bold=True)
        subtitle = render_text(self.controller.status_message, 25, theme.text_color)
        dots = "." * ((now_ms // 350) % 4)
        note = render_text(f"Ожидание соединения{dots}", 28, mix_color(theme.text_color, theme.accent_color, 0.25))
        self.screen.blit(title, (card.x + 54, card.y + 48))
        self.screen.blit(subtitle, (card.x + 56, card.y + 138))
        self.screen.blit(note, (card.x + 56, card.y + 198))

        self.buttons = self._build_buttons([("Назад", "back", "", False)], left=card.x + 56, top=card.bottom - 96, width=290, height=64)
        self._draw_buttons(theme, now_ms)

    def _draw_game(self, theme: ThemeConfig, now_ms: int) -> None:
        assert self.screen is not None
        layout = self._game_layout()
        self._draw_panel(layout.header, theme, glass=True, shadow=True)
        self._draw_panel(layout.board_frame, theme, glass=True, shadow=True)
        self._draw_panel(layout.sidebar, theme, glass=True, shadow=True)

        title = render_text("Reversi", 54, theme.accent_color, bold=True)
        self.screen.blit(title, (layout.header.x + 28, layout.header.y + 14))
        blit_text_block(
            self.screen,
            self._game_status_text(),
            layout.header.x + 30,
            layout.header.y + 58,
            layout.header.width - 340,
            22,
            theme.text_color,
            line_height=24,
            max_lines=2,
        )

        mode_label = self._mode_label()
        self._draw_tag(layout.header.right - 260, layout.header.y + 22, mode_label, theme)

        self._draw_board(layout.board, theme, now_ms)
        self._draw_sidebar(layout.sidebar, theme)
        self.buttons = self._build_buttons([("Назад в меню", "back", "", False)], left=layout.sidebar.x + 28, top=layout.sidebar.bottom - 84, width=layout.sidebar.width - 56, height=60)
        self._draw_buttons(theme, now_ms)

    def _game_layout(self) -> GameLayout:
        return GameLayout(
            header=pygame.Rect(56, 34, 1068, 96),
            board_frame=pygame.Rect(56, 150, 620, 620),
            board=pygame.Rect(86, 180, 560, 560),
            sidebar=pygame.Rect(710, 150, 414, 620),
        )

    def _draw_board(self, rect: pygame.Rect, theme: ThemeConfig, now_ms: int) -> None:
        assert self.screen is not None
        assert self.controller.game is not None
        game = self.controller.game
        board_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        cell_size = rect.width // game.size
        accent_grid = mix_color(theme.grid_color, theme.accent_color, 0.18)
        inner_board = pygame.Rect(0, 0, rect.width, rect.height)
        pygame.draw.rect(board_surface, mix_color(theme.board_color, theme.panel_color, 0.12), inner_board, border_radius=18)

        for row in range(game.size):
            for col in range(game.size):
                tint = 0.06 if (row + col) % 2 == 0 else 0.0
                cell_color = mix_color(theme.board_color, theme.panel_color, tint)
                cell_rect = pygame.Rect(col * cell_size, row * cell_size, cell_size, cell_size)
                pygame.draw.rect(board_surface, cell_color, cell_rect)

        for index in range(game.size + 1):
            offset = index * cell_size
            pygame.draw.line(board_surface, accent_grid, (offset, 0), (offset, rect.height), 2)
            pygame.draw.line(board_surface, accent_grid, (0, offset), (rect.width, offset), 2)

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
                        radius = cell_size // 8 + int(2 * animation_factor)
                        pygame.draw.circle(board_surface, theme.hint_color, cell_rect.center, radius)
                    continue

                disc_color = theme.black_disc_color if cell_value is Player.BLACK else theme.white_disc_color
                shadow_color = alpha_color((0, 0, 0), 70)
                radius = int(cell_size * 0.34)
                if self.pending_animation:
                    if (row, col) in self.pending_animation.flipped:
                        radius = int(radius * (0.50 + 0.50 * animation_factor))
                    elif self.pending_animation.position == (row, col):
                        radius = int(radius * (0.65 + 0.35 * animation_factor))
                shadow = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                pygame.draw.circle(shadow, shadow_color, (cell_size // 2 + 2, cell_size // 2 + 4), radius)
                board_surface.blit(shadow, cell_rect.topleft)
                pygame.draw.circle(board_surface, disc_color, cell_rect.center, radius)
                shine = mix_color(disc_color, theme.text_color, 0.35 if cell_value is Player.WHITE else 0.12)
                pygame.draw.circle(
                    board_surface,
                    shine,
                    (cell_rect.centerx - radius // 3, cell_rect.centery - radius // 3),
                    max(4, radius // 5),
                )

        self.screen.blit(board_surface, rect.topleft)
        self._draw_board_labels(rect, theme, orientation)

    def _draw_board_labels(self, rect: pygame.Rect, theme: ThemeConfig, orientation: Player) -> None:
        assert self.controller.game is not None
        letters = list("ABCDEFGH")
        numbers = [str(index) for index in range(1, self.controller.game.size + 1)]
        if orientation is Player.WHITE:
            letters.reverse()
            numbers.reverse()

        cell_size = rect.width // self.controller.game.size
        label_color = mix_color(theme.text_color, theme.accent_color, 0.22)
        for index, letter in enumerate(letters):
            label = render_text(letter, 20, label_color, bold=True)
            x_pos = rect.x + index * cell_size + cell_size // 2 - label.get_width() // 2
            self.screen.blit(label, (x_pos, rect.y - 28))
        for index, number in enumerate(numbers):
            label = render_text(number, 20, label_color, bold=True)
            y_pos = rect.y + index * cell_size + cell_size // 2 - label.get_height() // 2
            self.screen.blit(label, (rect.x - 24, y_pos))

    def _draw_sidebar(self, rect: pygame.Rect, theme: ThemeConfig) -> None:
        assert self.screen is not None
        assert self.controller.game is not None
        game = self.controller.game
        scores = game.scores()

        black_card = pygame.Rect(rect.x + 26, rect.y + 24, rect.width - 52, 72)
        white_card = pygame.Rect(rect.x + 26, rect.y + 110, rect.width - 52, 72)
        info_card = pygame.Rect(rect.x + 26, rect.y + 202, rect.width - 52, 126)

        for card in (black_card, white_card, info_card):
            self._draw_panel(card, theme, inner=True)

        self._draw_score_card(black_card, theme, Player.BLACK, scores[Player.BLACK])
        self._draw_score_card(white_card, theme, Player.WHITE, scores[Player.WHITE])

        lines = [
            ("Ход", game.current_player.display_name()),
            ("Доступные ходы", str(len(game.legal_moves(game.current_player)))),
        ]
        top = info_card.y + 18
        for label, value in lines:
            self.screen.blit(
                render_text(label, 19, mix_color(theme.text_color, theme.accent_color, 0.32), bold=True),
                (info_card.x + 20, top),
            )
            top = blit_text_block(
                self.screen,
                value,
                info_card.x + 20,
                top + 20,
                info_card.width - 40,
                22,
                theme.text_color,
                line_height=24,
                max_lines=2,
            )
            top += 8

    def _draw_score_card(self, rect: pygame.Rect, theme: ThemeConfig, player: Player, score: int) -> None:
        assert self.screen is not None
        color = theme.black_disc_color if player is Player.BLACK else theme.white_disc_color
        disc_center = (rect.x + 38, rect.y + rect.height // 2)
        pygame.draw.circle(self.screen, color, disc_center, 20)
        label = "Черные" if player is Player.BLACK else "Белые"
        self.screen.blit(render_text(label, 24, theme.text_color, bold=True), (rect.x + 70, rect.y + 16))
        score_surface = render_text(str(score), 34, theme.accent_color, bold=True)
        self.screen.blit(score_surface, (rect.right - 24 - score_surface.get_width(), rect.y + 14))

    def _draw_prompt(self, theme: ThemeConfig) -> None:
        assert self.screen is not None
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((4, 10, 10, 160))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(240, 230, 700, 260)
        self._draw_panel(panel, theme, glass=True, shadow=True, accent=True)
        title = render_text(self.controller.prompt.title, 38, theme.accent_color, bold=True)
        self.screen.blit(title, (panel.x + 34, panel.y + 26))
        if self.controller.prompt.purpose == "save_name":
            blit_text_block(
                self.screen,
                "Лучший результат. Введите имя для таблицы лидеров.",
                panel.x + 34,
                panel.y + 72,
                panel.width - 68,
                20,
                theme.text_color,
                line_height=22,
                max_lines=2,
            )

        field = pygame.Rect(panel.x + 34, panel.y + 108, panel.width - 68, 62)
        pygame.draw.rect(self.screen, mix_color(theme.panel_color, theme.board_color, 0.18), field, border_radius=16)
        pygame.draw.rect(self.screen, mix_color(theme.accent_color, theme.text_color, 0.10), field, width=2, border_radius=16)
        value = self.input_text or self.controller.prompt.placeholder
        self.screen.blit(render_text(value, 30, theme.text_color), (field.x + 18, field.y + 15))
        note_text = "Enter - сохранить, Esc - назад" if self.controller.prompt.purpose == "save_name" else "Enter - подтвердить, Esc - назад"
        note = render_text(note_text, 22, mix_color(theme.text_color, theme.accent_color, 0.26))
        self.screen.blit(note, (panel.x + 34, panel.y + 198))

    def _build_buttons(
        self,
        definitions: list[tuple[str, str, str, bool] | tuple[str, str, str] | tuple[str, str]],
        *,
        left: int = 60,
        top: int = 180,
        width: int = 380,
        height: int = 70,
        gap: int = 18,
    ) -> list[Button]:
        buttons = []
        for index, definition in enumerate(definitions):
            if len(definition) == 4:
                label, action, subtitle, primary = definition
            elif len(definition) == 3:
                label, action, subtitle = definition
                primary = False
            else:
                label, action = definition
                subtitle = ""
                primary = False
            rect = pygame.Rect(left, top + index * (height + gap), width, height)
            buttons.append(Button(label=label, rect=rect, action=action, subtitle=subtitle, primary=primary))
        return buttons

    def _draw_buttons(self, theme: ThemeConfig, now_ms: int) -> None:
        assert self.screen is not None
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            hovered = button.contains(mouse_pos)
            active = button.action == self.active_action and now_ms <= self.active_action_until
            if button.primary:
                fill = mix_color(theme.accent_color, theme.panel_color, 0.18 if hovered else 0.10)
                border = theme.accent_color
                text_color = mix_color((18, 26, 26), theme.background_color, 0.25)
            else:
                fill = mix_color(theme.panel_color, theme.board_color, 0.25 if hovered else 0.08)
                border = mix_color(theme.accent_color, theme.text_color, 0.12 if hovered else 0.30)
                text_color = theme.text_color
            if active:
                fill = mix_color(fill, theme.accent_color, 0.18)

            shadow_rect = button.rect.move(0, 6 if not active else 2)
            shadow = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 70), shadow.get_rect(), border_radius=18)
            self.screen.blit(shadow, shadow_rect.topleft)

            pygame.draw.rect(self.screen, fill, button.rect, border_radius=18)
            pygame.draw.rect(self.screen, border, button.rect, width=2, border_radius=18)
            label = render_text(button.label, 30, text_color, bold=True)
            label_x = button.rect.x + 18
            label_y = button.rect.y + (button.rect.height - label.get_height()) // 2 - 2
            self.screen.blit(label, (label_x, label_y))

    def _draw_panel(
        self,
        rect: pygame.Rect,
        theme: ThemeConfig,
        *,
        glass: bool = False,
        inner: bool = False,
        shadow: bool = False,
        accent: bool = False,
    ) -> None:
        assert self.screen is not None
        if shadow:
            shadow_surface = pygame.Surface((rect.width + 18, rect.height + 18), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surface, (0, 0, 0, 80), shadow_surface.get_rect(), border_radius=28)
            self.screen.blit(shadow_surface, (rect.x - 4, rect.y + 8))

        if glass:
            fill = alpha_color(mix_color(theme.panel_color, theme.background_color, 0.25), 225)
        elif inner:
            fill = alpha_color(mix_color(theme.panel_color, theme.board_color, 0.16), 245)
        else:
            fill = alpha_color(theme.panel_color, 255)

        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=24)
        border_color = theme.accent_color if accent else mix_color(theme.accent_color, theme.text_color, 0.22)
        pygame.draw.rect(panel, alpha_color(border_color, 210), panel.get_rect(), width=2, border_radius=24)
        highlight = pygame.Rect(16, 12, rect.width - 32, max(22, rect.height // 7))
        pygame.draw.rect(panel, alpha_color(mix_color(theme.text_color, theme.panel_color, 0.55), 24), highlight, border_radius=18)
        self.screen.blit(panel, rect.topleft)

    def _draw_tag(self, x_pos: int, y_pos: int, text: str, theme: ThemeConfig) -> None:
        assert self.screen is not None
        label = render_text(text, 20, mix_color((24, 24, 18), theme.background_color, 0.05), bold=True)
        rect = pygame.Rect(x_pos, y_pos, label.get_width() + 28, label.get_height() + 12)
        pygame.draw.rect(self.screen, theme.accent_color, rect, border_radius=15)
        self.screen.blit(label, (rect.x + 14, rect.y + 6))

    def _draw_disc_pattern(self, rect: pygame.Rect, theme: ThemeConfig) -> None:
        assert self.screen is not None
        positions = [
            (rect.right - 180, rect.y + 96, theme.black_disc_color),
            (rect.right - 122, rect.y + 146, theme.white_disc_color),
            (rect.right - 238, rect.y + 152, theme.black_disc_color),
            (rect.right - 176, rect.y + 204, theme.white_disc_color),
        ]
        for x_pos, y_pos, color in positions:
            pygame.draw.circle(self.screen, color, (x_pos, y_pos), 24)
            pygame.draw.circle(self.screen, mix_color(color, theme.text_color, 0.2), (x_pos - 8, y_pos - 8), 7)

    def _draw_info_lines(
        self,
        rect: pygame.Rect,
        lines: list[str],
        theme: ThemeConfig,
        *,
        title_size: int = 26,
    ) -> None:
        assert self.screen is not None
        top = rect.y + 24
        for index, line in enumerate(lines):
            size = title_size if index == 0 else 22
            color = theme.accent_color if index == 0 else theme.text_color
            bold = index == 0
            self.screen.blit(render_text(line, size, color, bold=bold), (rect.x + 22, top))
            top += 42 if index == 0 else 30

    def _mode_label(self) -> str:
        labels = {
            GameMode.PRACTICE: "Тренировка",
            GameMode.VS_AI: "С компьютером",
            GameMode.LOCAL_TWO: "Два игрока",
            GameMode.ONLINE_HOST: "Онлайн host",
            GameMode.ONLINE_JOIN: "Онлайн join",
        }
        if self.controller.mode is None:
            return "Без режима"
        return labels.get(self.controller.mode, self.controller.mode.value)

    def _game_status_text(self) -> str:
        game = self.controller.game
        if game is None:
            return self.controller.status_message

        if game.game_over:
            winner = game.winner()
            return f"Победа: {winner.display_name()}" if winner else "Ничья"

        if "пропущен" in self.controller.status_message.lower():
            return "Ход пропущен"

        if self.controller.mode is GameMode.VS_AI:
            return "Ваш ход" if game.current_player is self.controller.local_player else "Ход компьютера"

        return f"Ход: {game.current_player.display_name()}"

    def _help_body_text(self) -> str:
        parts = self.controller.help_text.split("\n\n", 1)
        if len(parts) == 2:
            return parts[1]
        return self.controller.help_text

    def _board_position_from_mouse(self, position: tuple[int, int]) -> tuple[int, int] | None:
        if not self.controller.game:
            return None
        board_rect = self._game_layout().board
        if not board_rect.collidepoint(position):
            return None
        cell_size = board_rect.width // self.controller.game.size
        col = (position[0] - board_rect.left) // cell_size
        row = (position[1] - board_rect.top) // cell_size
        return row, col


def run_app(base_dir: Path | str) -> None:  # pragma: no cover
    app = PygameReversiApp(base_dir)
    app.run()
