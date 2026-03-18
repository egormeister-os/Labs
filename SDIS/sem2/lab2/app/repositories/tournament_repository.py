from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Sequence

from app.models import SearchCriteria, TournamentRecord, TournamentRecordInput, ValidationError


class TournamentRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.connection: sqlite3.Connection | None = None
        self.database_path = Path(database_path)
        self.switch_database(self.database_path)

    def switch_database(self, database_path: str | Path) -> None:
        if self.connection is not None:
            self.connection.close()

        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.database_path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.create_function("CASEFOLD", 1, self._casefold)
        self._initialize_schema()

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def _initialize_schema(self) -> None:
        assert self.connection is not None
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tournaments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tournament_name TEXT NOT NULL,
                event_date DATE NOT NULL,
                sport_name TEXT NOT NULL,
                winner_full_name TEXT NOT NULL,
                prize_amount REAL NOT NULL CHECK(prize_amount >= 0),
                winner_earnings REAL NOT NULL CHECK(winner_earnings >= 0)
            )
            """
        )
        self.connection.commit()

    def add_record(self, record_input: TournamentRecordInput) -> TournamentRecord:
        assert self.connection is not None
        record = record_input.to_record()
        cursor = self.connection.execute(
            """
            INSERT INTO tournaments (
                tournament_name,
                event_date,
                sport_name,
                winner_full_name,
                prize_amount,
                winner_earnings
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                record.tournament_name,
                record.event_date.isoformat(),
                record.sport_name,
                record.winner_full_name,
                record.prize_amount,
                record.winner_earnings,
            ),
        )
        self.connection.commit()
        return TournamentRecord(
            id=int(cursor.lastrowid),
            tournament_name=record.tournament_name,
            event_date=record.event_date,
            sport_name=record.sport_name,
            winner_full_name=record.winner_full_name,
            prize_amount=record.prize_amount,
            winner_earnings=record.winner_earnings,
        )

    def count_records(self) -> int:
        assert self.connection is not None
        cursor = self.connection.execute("SELECT COUNT(*) FROM tournaments")
        return int(cursor.fetchone()[0])

    def get_page(self, limit: int, offset: int) -> list[TournamentRecord]:
        assert self.connection is not None
        cursor = self.connection.execute(
            """
            SELECT *
            FROM tournaments
            ORDER BY event_date DESC, tournament_name ASC, id ASC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        return [self._row_to_record(row) for row in cursor.fetchall()]

    def search_count(self, criteria: SearchCriteria) -> int:
        assert self.connection is not None
        where_sql, params = self._build_where_clause(criteria)
        cursor = self.connection.execute(
            f"SELECT COUNT(*) FROM tournaments {where_sql}",
            params,
        )
        return int(cursor.fetchone()[0])

    def search_page(
        self,
        criteria: SearchCriteria,
        limit: int,
        offset: int,
    ) -> list[TournamentRecord]:
        assert self.connection is not None
        where_sql, params = self._build_where_clause(criteria)
        cursor = self.connection.execute(
            f"""
            SELECT *
            FROM tournaments
            {where_sql}
            ORDER BY event_date DESC, tournament_name ASC, id ASC
            LIMIT ? OFFSET ?
            """,
            [*params, limit, offset],
        )
        return [self._row_to_record(row) for row in cursor.fetchall()]

    def delete_by_criteria(self, criteria: SearchCriteria) -> int:
        assert self.connection is not None
        normalized = criteria.normalized()
        if normalized.is_empty():
            raise ValidationError("Для удаления необходимо задать хотя бы одно условие.")

        where_sql, params = self._build_where_clause(normalized)
        cursor = self.connection.execute(
            f"DELETE FROM tournaments {where_sql}",
            params,
        )
        self.connection.commit()
        return int(cursor.rowcount)

    def replace_all(self, records: Sequence[TournamentRecord]) -> None:
        assert self.connection is not None
        with self.connection:
            self.connection.execute("DELETE FROM tournaments")
            self.connection.executemany(
                """
                INSERT INTO tournaments (
                    tournament_name,
                    event_date,
                    sport_name,
                    winner_full_name,
                    prize_amount,
                    winner_earnings
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        record.tournament_name,
                        record.event_date.isoformat(),
                        record.sport_name,
                        record.winner_full_name,
                        record.prize_amount,
                        record.winner_earnings,
                    )
                    for record in records
                ],
            )

    def get_all_records(self) -> list[TournamentRecord]:
        assert self.connection is not None
        cursor = self.connection.execute(
            """
            SELECT *
            FROM tournaments
            ORDER BY event_date DESC, tournament_name ASC, id ASC
            """
        )
        return [self._row_to_record(row) for row in cursor.fetchall()]

    def get_unique_sports(self) -> list[str]:
        assert self.connection is not None
        cursor = self.connection.execute(
            """
            SELECT DISTINCT sport_name
            FROM tournaments
            WHERE sport_name <> ''
            ORDER BY sport_name COLLATE NOCASE ASC
            """
        )
        return [str(row["sport_name"]) for row in cursor.fetchall()]

    def save_as(self, target_path: str | Path) -> None:
        records = self.get_all_records()
        target_repository = TournamentRepository(target_path)
        try:
            target_repository.replace_all(records)
        finally:
            target_repository.close()

    def _build_where_clause(self, criteria: SearchCriteria) -> tuple[str, list[object]]:
        normalized = criteria.normalized()
        clauses: list[str] = []
        params: list[object] = []

        if normalized.tournament_name:
            clauses.append("CASEFOLD(tournament_name) LIKE ?")
            params.append(f"%{normalized.tournament_name.casefold()}%")
        if normalized.event_date is not None:
            clauses.append("event_date = ?")
            params.append(normalized.event_date.isoformat())
        if normalized.sport_name:
            clauses.append("sport_name = ?")
            params.append(normalized.sport_name)
        if normalized.winner_name_fragment:
            clauses.append("CASEFOLD(winner_full_name) LIKE ?")
            params.append(f"%{normalized.winner_name_fragment.casefold()}%")
        if normalized.min_prize_amount is not None:
            clauses.append("prize_amount >= ?")
            params.append(normalized.min_prize_amount)
        if normalized.max_prize_amount is not None:
            clauses.append("prize_amount <= ?")
            params.append(normalized.max_prize_amount)
        if normalized.min_winner_earnings is not None:
            clauses.append("winner_earnings >= ?")
            params.append(normalized.min_winner_earnings)
        if normalized.max_winner_earnings is not None:
            clauses.append("winner_earnings <= ?")
            params.append(normalized.max_winner_earnings)

        if not clauses:
            return "", params
        return f"WHERE {' AND '.join(clauses)}", params

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> TournamentRecord:
        return TournamentRecord(
            id=int(row["id"]),
            tournament_name=str(row["tournament_name"]),
            event_date=TournamentRepository._parse_date(str(row["event_date"])),
            sport_name=str(row["sport_name"]),
            winner_full_name=str(row["winner_full_name"]),
            prize_amount=round(float(row["prize_amount"]), 2),
            winner_earnings=round(float(row["winner_earnings"]), 2),
        )

    @staticmethod
    def _parse_date(value: str):
        from datetime import date

        return date.fromisoformat(value)

    @staticmethod
    def _casefold(value: object) -> str:
        return str(value).casefold()
