from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import ceil

EARNINGS_RATIO = 0.6


class ValidationError(ValueError):
    """Raised when user-entered data does not satisfy business rules."""


def compute_winner_earnings(prize_amount: float) -> float:
    return round(prize_amount * EARNINGS_RATIO, 2)


def _require_text(value: str, field_title: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError(f'Поле "{field_title}" должно быть заполнено.')
    return cleaned


def _require_non_negative_number(value: float, field_title: str) -> float:
    if value < 0:
        raise ValidationError(f'Поле "{field_title}" не может быть отрицательным.')
    return round(float(value), 2)


@dataclass(slots=True, frozen=True)
class TournamentRecordInput:
    tournament_name: str
    event_date: date
    sport_name: str
    winner_full_name: str
    prize_amount: float

    def normalized(self) -> "TournamentRecordInput":
        if not isinstance(self.event_date, date):
            raise ValidationError('Поле "Дата проведения" должно содержать корректную дату.')

        return TournamentRecordInput(
            tournament_name=_require_text(self.tournament_name, "Название турнира"),
            event_date=self.event_date,
            sport_name=_require_text(self.sport_name, "Название вида спорта"),
            winner_full_name=_require_text(self.winner_full_name, "ФИО победителя"),
            prize_amount=_require_non_negative_number(
                self.prize_amount,
                "Размер призовых турнира",
            ),
        )

    def to_record(self, record_id: int | None = None) -> "TournamentRecord":
        normalized = self.normalized()
        return TournamentRecord(
            id=record_id,
            tournament_name=normalized.tournament_name,
            event_date=normalized.event_date,
            sport_name=normalized.sport_name,
            winner_full_name=normalized.winner_full_name,
            prize_amount=normalized.prize_amount,
            winner_earnings=compute_winner_earnings(normalized.prize_amount),
        )


@dataclass(slots=True, frozen=True)
class TournamentRecord:
    id: int | None
    tournament_name: str
    event_date: date
    sport_name: str
    winner_full_name: str
    prize_amount: float
    winner_earnings: float

    def as_tuple(self) -> tuple[str, str, str, str, str, str]:
        return (
            self.tournament_name,
            self.event_date.strftime("%d.%m.%Y"),
            self.sport_name,
            self.winner_full_name,
            f"{self.prize_amount:,.2f}".replace(",", " "),
            f"{self.winner_earnings:,.2f}".replace(",", " "),
        )


@dataclass(slots=True, frozen=True)
class SearchCriteria:
    tournament_name: str = ""
    event_date: date | None = None
    sport_name: str = ""
    winner_name_fragment: str = ""
    min_prize_amount: float | None = None
    max_prize_amount: float | None = None
    min_winner_earnings: float | None = None
    max_winner_earnings: float | None = None

    def normalized(self) -> "SearchCriteria":
        normalized = SearchCriteria(
            tournament_name=self.tournament_name.strip(),
            event_date=self.event_date,
            sport_name=self.sport_name.strip(),
            winner_name_fragment=self.winner_name_fragment.strip(),
            min_prize_amount=(
                round(float(self.min_prize_amount), 2)
                if self.min_prize_amount is not None
                else None
            ),
            max_prize_amount=(
                round(float(self.max_prize_amount), 2)
                if self.max_prize_amount is not None
                else None
            ),
            min_winner_earnings=(
                round(float(self.min_winner_earnings), 2)
                if self.min_winner_earnings is not None
                else None
            ),
            max_winner_earnings=(
                round(float(self.max_winner_earnings), 2)
                if self.max_winner_earnings is not None
                else None
            ),
        )
        normalized.validate_ranges()
        return normalized

    def validate_ranges(self) -> None:
        if (
            self.min_prize_amount is not None
            and self.max_prize_amount is not None
            and self.min_prize_amount > self.max_prize_amount
        ):
            raise ValidationError(
                "Нижняя граница размера призовых не может быть больше верхней."
            )
        if (
            self.min_winner_earnings is not None
            and self.max_winner_earnings is not None
            and self.min_winner_earnings > self.max_winner_earnings
        ):
            raise ValidationError(
                "Нижняя граница заработка победителя не может быть больше верхней."
            )

    def is_empty(self) -> bool:
        return not any(
            (
                self.tournament_name,
                self.event_date,
                self.sport_name,
                self.winner_name_fragment,
                self.min_prize_amount is not None,
                self.max_prize_amount is not None,
                self.min_winner_earnings is not None,
                self.max_winner_earnings is not None,
            )
        )


@dataclass(slots=True, frozen=True)
class PageResult:
    items: list[TournamentRecord]
    page: int
    page_size: int
    total_count: int

    @property
    def total_pages(self) -> int:
        if self.total_count <= 0:
            return 1
        return ceil(self.total_count / self.page_size)

    @property
    def current_page_count(self) -> int:
        return len(self.items)
