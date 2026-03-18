from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.controllers import AppController
from app.models import SearchCriteria
from app.repositories import TournamentRepository
from app.services import TournamentXmlReader, TournamentXmlWriter


def test_xml_writer_and_reader_roundtrip(tmp_path, sample_records):
    target = tmp_path / "nested" / "records.xml"
    writer = TournamentXmlWriter()
    reader = TournamentXmlReader()

    writer.write(target, sample_records)

    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert 'count="3"' in content
    assert "<winner_earnings>" in content

    restored_records = reader.read(target)
    assert len(restored_records) == 3
    assert restored_records[0].tournament_name == sample_records[0].tournament_name
    assert restored_records[0].winner_earnings == sample_records[0].winner_earnings


def test_xml_reader_raises_for_missing_required_field(tmp_path):
    broken_xml = tmp_path / "broken.xml"
    broken_xml.write_text(
        """
        <tournaments count="1">
          <tournament>
            <tournament_name>Broken</tournament_name>
            <sport_name>Tennis</sport_name>
            <winner_full_name>Игрок</winner_full_name>
            <prize_amount>100.00</prize_amount>
          </tournament>
        </tournaments>
        """,
        encoding="utf-8",
    )

    with pytest.raises(KeyError):
        TournamentXmlReader().read(broken_xml)


def test_controller_get_records_page_search_export_import_and_save(tmp_path, sample_inputs):
    controller = AppController(tmp_path / "source.db")
    try:
        empty_page = controller.get_records_page(page=5, page_size=10)
        assert empty_page.page == 1
        assert empty_page.total_count == 0

        for record_input in sample_inputs:
            controller.add_record(record_input)

        overflown_page = controller.get_records_page(page=99, page_size=2)
        assert overflown_page.page == 2
        assert overflown_page.current_page_count == 1

        search_page = controller.search_records(SearchCriteria(sport_name="Tennis"), page=1, page_size=10)
        assert search_page.total_count == 2
        assert controller.get_unique_sports() == ["Football", "Tennis"]

        xml_path = tmp_path / "export.xml"
        assert controller.export_to_xml(xml_path) == 3
        assert xml_path.exists()

        other_database = tmp_path / "other.db"
        controller.open_database(other_database)
        assert controller.current_database_path == other_database
        assert controller.get_records_page(1, 10).total_count == 0

        imported_count = controller.import_from_xml(xml_path)
        assert imported_count == 3
        assert controller.get_records_page(1, 10).total_count == 3

        saved_database = tmp_path / "saved_copy.db"
        controller.save_database_as(saved_database)
        assert controller.current_database_path == saved_database
        assert controller.get_records_page(1, 10).total_count == 3
    finally:
        controller.close()

    copied_repository = TournamentRepository(saved_database)
    try:
        assert copied_repository.count_records() == 3
    finally:
        copied_repository.close()


@pytest.mark.parametrize(
    ("page", "page_size", "total_count", "expected"),
    [
        (0, 10, 100, 1),
        (4, 10, 0, 1),
        (9, 10, 25, 3),
        (2, 0, 25, 1),
    ],
)
def test_controller_normalize_page(page, page_size, total_count, expected):
    assert AppController._normalize_page(page, page_size, total_count) == expected
