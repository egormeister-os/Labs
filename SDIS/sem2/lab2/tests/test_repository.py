from __future__ import annotations

from datetime import date

import pytest

from app.models import SearchCriteria, ValidationError
from app.repositories import TournamentRepository


def test_repository_add_count_and_get_page(repository):
    assert repository.count_records() == 3

    first_page = repository.get_page(limit=2, offset=0)
    second_page = repository.get_page(limit=2, offset=2)

    assert len(first_page) == 2
    assert first_page[0].tournament_name == "Открытый Брест"
    assert first_page[1].tournament_name == "Кубок Минска"
    assert len(second_page) == 1
    assert second_page[0].tournament_name == "Зимний Кубок"


def test_repository_search_supports_casefold_date_and_ranges(repository):
    criteria = SearchCriteria(
        tournament_name="кубок",
        event_date=date(2025, 1, 10),
        sport_name="Tennis",
        winner_name_fragment="иван",
        min_prize_amount=900,
        max_prize_amount=1100,
        min_winner_earnings=600,
        max_winner_earnings=600,
    )

    assert repository.search_count(criteria) == 1

    items = repository.search_page(criteria, limit=10, offset=0)
    assert len(items) == 1
    assert items[0].winner_full_name == "Иванов Иван Иванович"


def test_repository_delete_by_criteria_and_empty_validation(repository):
    with pytest.raises(ValidationError):
        repository.delete_by_criteria(SearchCriteria())

    deleted = repository.delete_by_criteria(SearchCriteria(sport_name="Tennis"))
    assert deleted == 2
    assert repository.count_records() == 1

    deleted_again = repository.delete_by_criteria(SearchCriteria(tournament_name="несуществующий"))
    assert deleted_again == 0


def test_repository_replace_all_and_get_all_records(repository, make_input):
    new_record = make_input(
        tournament_name="Новый турнир",
        event_date=date(2026, 1, 1),
        sport_name="Chess",
        winner_full_name="Новый Победитель",
        prize_amount=5555,
    ).to_record()

    repository.replace_all([new_record])
    all_records = repository.get_all_records()

    assert len(all_records) == 1
    assert all_records[0].tournament_name == "Новый турнир"
    assert repository.get_unique_sports() == ["Chess"]


def test_repository_save_as_copies_records(repository, tmp_path):
    target_path = tmp_path / "copy.sqlite3"
    repository.save_as(target_path)

    copied_repository = TournamentRepository(target_path)
    try:
        assert copied_repository.count_records() == 3
        assert len(copied_repository.get_all_records()) == 3
    finally:
        copied_repository.close()


def test_repository_switch_database_and_helpers(repository, tmp_path):
    other_path = tmp_path / "other.db"
    repository.switch_database(other_path)

    assert repository.database_path == other_path
    assert repository.count_records() == 0
    assert TournamentRepository._parse_date("2025-05-20") == date(2025, 5, 20)
    assert TournamentRepository._casefold("ИВАН") == "иван"


def test_repository_close_sets_connection_to_none(repository):
    repository.close()
    assert repository.connection is None
