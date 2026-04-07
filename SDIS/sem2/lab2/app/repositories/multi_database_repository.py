from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from app.models import (
    SearchCriteria,
    TournamentRecord,
    TournamentRecordInput,
    ValidationError,
)

from .tournament_repository import TournamentRepository


class MultiDatabaseTournamentRepository:
    def __init__(self, database_paths: str | Path | Sequence[str | Path]) -> None:
        self.repositories: list[TournamentRepository] = []
        self.xml_sources: list[_XmlRecordSource] = []
        self.open_databases(database_paths)

    @property
    def database_path(self) -> Path:
        return self.primary_repository.database_path

    @property
    def database_paths(self) -> tuple[Path, ...]:
        return tuple(repository.database_path for repository in self.repositories)

    @property
    def xml_source_paths(self) -> tuple[Path, ...]:
        return tuple(source.source_path for source in self.xml_sources)

    @property
    def source_paths(self) -> tuple[Path, ...]:
        return (*self.database_paths, *self.xml_source_paths)

    @property
    def primary_repository(self) -> TournamentRepository:
        if not self.repositories:
            raise RuntimeError("Не открыто ни одной базы данных.")
        return self.repositories[0]

    def open_databases(self, database_paths: str | Path | Sequence[str | Path]) -> None:
        normalized_paths = self._normalize_paths(database_paths)
        if not normalized_paths:
            raise ValueError("Не выбрано ни одной базы данных.")

        self.close()
        self.repositories = [TournamentRepository(path) for path in normalized_paths]
        self.xml_sources = []

    def switch_database(self, database_path: str | Path) -> None:
        self.open_databases([database_path])

    def add_record(self, record_input: TournamentRecordInput) -> TournamentRecord:
        return self.primary_repository.add_record(record_input)

    def count_records(self) -> int:
        return len(self.get_all_records())

    def get_page(self, limit: int, offset: int) -> list[TournamentRecord]:
        return self.get_all_records()[offset : offset + max(limit, 0)]

    def search_count(self, criteria: SearchCriteria) -> int:
        return len(self._filter_records(criteria))

    def search_page(
        self,
        criteria: SearchCriteria,
        limit: int,
        offset: int,
    ) -> list[TournamentRecord]:
        return self._filter_records(criteria)[offset : offset + max(limit, 0)]

    def delete_by_criteria(self, criteria: SearchCriteria) -> int:
        deleted_from_databases = sum(
            repository.delete_by_criteria(criteria)
            for repository in self.repositories
        )
        deleted_from_xml = sum(
            source.delete_by_criteria(criteria)
            for source in self.xml_sources
        )
        return deleted_from_databases + deleted_from_xml

    def replace_all(self, records: Sequence[TournamentRecord]) -> None:
        self.primary_repository.replace_all(records)

    def get_all_records(self) -> list[TournamentRecord]:
        records = [
            record
            for source in (*self.repositories, *self.xml_sources)
            for record in source.get_all_records()
        ]
        return self._deduplicate_records(records)

    def get_unique_sports(self) -> list[str]:
        sports = {
            record.sport_name.strip()
            for record in self.get_all_records()
            if record.sport_name.strip()
        }
        return sorted(sports, key=str.casefold)

    def save_as(self, target_path: str | Path) -> None:
        target_repository = TournamentRepository(target_path)
        try:
            target_repository.replace_all(self.get_all_records())
        finally:
            target_repository.close()

    def add_xml_sources(
        self,
        xml_sources: Sequence[tuple[str | Path, Sequence[TournamentRecord]]],
    ) -> None:
        normalized_sources = [
            _XmlRecordSource(source_path, records)
            for source_path, records in xml_sources
        ]
        if not normalized_sources:
            raise ValueError("Не выбрано ни одного XML-файла.")

        existing_by_path = {
            source.source_path: source
            for source in self.xml_sources
        }
        for source in normalized_sources:
            existing_by_path[source.source_path] = source
        self.xml_sources = list(existing_by_path.values())

    def clear_xml_sources(self) -> None:
        self.xml_sources = []

    def close(self) -> None:
        for repository in self.repositories:
            repository.close()
        self.repositories = []
        self.xml_sources = []

    def _filter_records(self, criteria: SearchCriteria) -> list[TournamentRecord]:
        normalized = criteria.normalized()
        return [
            record
            for record in self.get_all_records()
            if self._matches_criteria(record, normalized)
        ]

    @staticmethod
    def _deduplicate_records(records: list[TournamentRecord]) -> list[TournamentRecord]:
        unique_records: list[TournamentRecord] = []
        seen_keys: set[tuple[object, ...]] = set()

        for record in sorted(
            records,
            key=lambda item: (
                -item.event_date.toordinal(),
                item.tournament_name.casefold(),
                item.sport_name.casefold(),
                item.winner_full_name.casefold(),
                item.prize_amount,
                item.winner_earnings,
                item.id or 0,
            ),
        ):
            record_key = record.identity_key()
            if record_key in seen_keys:
                continue
            seen_keys.add(record_key)
            unique_records.append(record)

        return unique_records

    @staticmethod
    def _matches_criteria(record: TournamentRecord, criteria: SearchCriteria) -> bool:
        if criteria.tournament_name and criteria.tournament_name.casefold() not in record.tournament_name.casefold():
            return False
        if criteria.event_date is not None and record.event_date != criteria.event_date:
            return False
        if criteria.sport_name and record.sport_name != criteria.sport_name:
            return False
        if (
            criteria.winner_name_fragment
            and criteria.winner_name_fragment.casefold() not in record.winner_full_name.casefold()
        ):
            return False
        if criteria.min_prize_amount is not None and record.prize_amount < criteria.min_prize_amount:
            return False
        if criteria.max_prize_amount is not None and record.prize_amount > criteria.max_prize_amount:
            return False
        if (
            criteria.min_winner_earnings is not None
            and record.winner_earnings < criteria.min_winner_earnings
        ):
            return False
        if (
            criteria.max_winner_earnings is not None
            and record.winner_earnings > criteria.max_winner_earnings
        ):
            return False
        return True

    @staticmethod
    def _normalize_paths(
        database_paths: str | Path | Sequence[str | Path],
    ) -> list[Path]:
        if isinstance(database_paths, (str, Path)):
            raw_paths = [database_paths]
        else:
            raw_paths = list(database_paths)

        unique_paths: list[Path] = []
        seen_paths: set[Path] = set()
        for raw_path in raw_paths:
            normalized_path = Path(raw_path).expanduser().resolve()
            if normalized_path in seen_paths:
                continue
            seen_paths.add(normalized_path)
            unique_paths.append(normalized_path)
        return unique_paths


class _XmlRecordSource:
    def __init__(
        self,
        source_path: str | Path,
        records: Sequence[TournamentRecord],
    ) -> None:
        self.source_path = Path(source_path).expanduser().resolve()
        self.records = list(records)

    def get_all_records(self) -> list[TournamentRecord]:
        return list(self.records)

    def delete_by_criteria(self, criteria: SearchCriteria) -> int:
        normalized = criteria.normalized()
        if normalized.is_empty():
            raise ValidationError("Для удаления необходимо задать хотя бы одно условие.")

        original_count = len(self.records)
        self.records = [
            record
            for record in self.records
            if not MultiDatabaseTournamentRepository._matches_criteria(record, normalized)
        ]
        return original_count - len(self.records)
