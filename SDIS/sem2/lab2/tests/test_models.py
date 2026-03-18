from __future__ import annotations

from datetime import date

import pytest

from app.models import (
    EARNINGS_RATIO,
    PageResult,
    SearchCriteria,
    TournamentRecord,
    TournamentRecordInput,
    ValidationError,
    compute_winner_earnings,
)


def test_compute_winner_earnings_rounds_to_two_decimals():
    assert EARNINGS_RATIO == 0.6
    assert compute_winner_earnings(1000) == 600.0
    assert compute_winner_earnings(3333.335) == 2000.0


def test_tournament_record_input_normalized_trims_values(make_input):
    normalized = make_input(
        tournament_name="  Кубок Минска  ",
        sport_name="  Tennis  ",
        winner_full_name="  Иванов Иван Иванович  ",
        prize_amount=1000.456,
    ).normalized()

    assert normalized.tournament_name == "Кубок Минска"
    assert normalized.sport_name == "Tennis"
    assert normalized.winner_full_name == "Иванов Иван Иванович"
    assert normalized.prize_amount == 1000.46


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("tournament_name", "  "),
        ("sport_name", ""),
        ("winner_full_name", " "),
    ],
)
def test_tournament_record_input_rejects_empty_text_fields(make_input, field_name, value):
    kwargs = {field_name: value}
    with pytest.raises(ValidationError):
        make_input(**kwargs).normalized()


def test_tournament_record_input_rejects_invalid_date(make_input):
    with pytest.raises(ValidationError):
        TournamentRecordInput(
            tournament_name="Кубок",
            event_date="2025-01-01",
            sport_name="Tennis",
            winner_full_name="Иванов Иван Иванович",
            prize_amount=1000.0,
        ).normalized()


def test_tournament_record_input_rejects_negative_prize(make_input):
    with pytest.raises(ValidationError):
        make_input(prize_amount=-1).normalized()


def test_tournament_record_to_record_computes_earnings_and_formats_tuple(make_input):
    record = make_input(prize_amount=12345.5).to_record(record_id=7)

    assert record == TournamentRecord(
        id=7,
        tournament_name="Кубок Минска",
        event_date=date(2025, 2, 10),
        sport_name="Tennis",
        winner_full_name="Иванов Иван Иванович",
        prize_amount=12345.5,
        winner_earnings=7407.3,
    )
    assert record.as_tuple() == (
        "Кубок Минска",
        "10.02.2025",
        "Tennis",
        "Иванов Иван Иванович",
        "12 345.50",
        "7 407.30",
    )


def test_search_criteria_normalized_and_is_empty():
    empty = SearchCriteria()
    assert empty.is_empty() is True

    criteria = SearchCriteria(
        tournament_name="  Кубок  ",
        sport_name="  Tennis  ",
        winner_name_fragment="  Иван  ",
        min_prize_amount=10,
        max_prize_amount=20.556,
        min_winner_earnings=1,
        max_winner_earnings=2.556,
    ).normalized()

    assert criteria.is_empty() is False
    assert criteria.tournament_name == "Кубок"
    assert criteria.sport_name == "Tennis"
    assert criteria.winner_name_fragment == "Иван"
    assert criteria.max_prize_amount == 20.56
    assert criteria.max_winner_earnings == 2.56


def test_search_criteria_rejects_invalid_ranges():
    with pytest.raises(ValidationError):
        SearchCriteria(min_prize_amount=100, max_prize_amount=50).normalized()

    with pytest.raises(ValidationError):
        SearchCriteria(min_winner_earnings=20, max_winner_earnings=10).normalized()


def test_page_result_reports_pages_and_current_page_count(sample_records):
    page_result = PageResult(items=sample_records[:2], page=1, page_size=2, total_count=3)
    empty_result = PageResult(items=[], page=1, page_size=10, total_count=0)

    assert page_result.total_pages == 2
    assert page_result.current_page_count == 2
    assert empty_result.total_pages == 1
    assert empty_result.current_page_count == 0
