from __future__ import annotations

from pathlib import Path
from collections.abc import Sequence

from app.models import PageResult, SearchCriteria, TournamentRecord, TournamentRecordInput
from app.repositories import MultiDatabaseTournamentRepository
from app.services import TournamentXmlReader, TournamentXmlWriter


class AppController:
    def __init__(self, database_path: str | Path | Sequence[str | Path]) -> None:
        self.repository = MultiDatabaseTournamentRepository(database_path)
        self.xml_reader = TournamentXmlReader()
        self.xml_writer = TournamentXmlWriter()

    @property
    def current_database_path(self) -> Path:
        return self.repository.database_path

    @property
    def opened_database_paths(self) -> tuple[Path, ...]:
        return self.repository.database_paths

    @property
    def opened_xml_paths(self) -> tuple[Path, ...]:
        return self.repository.xml_source_paths

    @property
    def opened_source_paths(self) -> tuple[Path, ...]:
        return self.repository.source_paths

    def add_record(self, record_input: TournamentRecordInput) -> TournamentRecord:
        return self.repository.add_record(record_input)

    def get_records_page(self, page: int, page_size: int) -> PageResult:
        total_count = self.repository.count_records()
        safe_page = self._normalize_page(page, page_size, total_count)
        offset = (safe_page - 1) * page_size
        items = self.repository.get_page(page_size, offset) if total_count else []
        return PageResult(items=items, page=safe_page, page_size=page_size, total_count=total_count)

    def search_records(
        self,
        criteria: SearchCriteria,
        page: int,
        page_size: int,
    ) -> PageResult:
        total_count = self.repository.search_count(criteria)
        safe_page = self._normalize_page(page, page_size, total_count)
        offset = (safe_page - 1) * page_size
        items = self.repository.search_page(criteria, page_size, offset) if total_count else []
        return PageResult(items=items, page=safe_page, page_size=page_size, total_count=total_count)

    def delete_records(self, criteria: SearchCriteria) -> int:
        return self.repository.delete_by_criteria(criteria)

    def get_unique_sports(self) -> list[str]:
        return self.repository.get_unique_sports()

    def export_to_xml(self, target_path: str | Path) -> int:
        records = self.repository.get_all_records()
        self.xml_writer.write(target_path, records)
        return len(records)

    def import_from_xml(self, source_path: str | Path) -> int:
        records = self.xml_reader.read(source_path)
        self.repository.replace_all(records)
        return len(records)

    def import_xml_sources(self, source_paths: Sequence[str | Path]) -> int:
        if not source_paths:
            raise ValueError("Не выбрано ни одного XML-файла.")

        xml_sources = []
        total_count = 0
        for source_path in source_paths:
            records = self.xml_reader.read(source_path)
            xml_sources.append((source_path, records))
            total_count += len(records)

        self.repository.add_xml_sources(xml_sources)
        return total_count

    def open_database(self, database_path: str | Path) -> None:
        self.repository.switch_database(database_path)

    def open_databases(self, database_paths: Sequence[str | Path]) -> None:
        self.repository.open_databases(database_paths)

    def save_database_as(self, database_path: str | Path) -> None:
        self.repository.save_as(database_path)
        self.repository.switch_database(database_path)

    def close(self) -> None:
        self.repository.close()

    @staticmethod
    def _normalize_page(page: int, page_size: int, total_count: int) -> int:
        if page_size <= 0:
            return 1
        if total_count <= 0:
            return 1
        total_pages = max(1, -(-total_count // page_size))
        return max(1, min(page, total_pages))
