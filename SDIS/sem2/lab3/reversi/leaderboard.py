from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class LeaderboardEntry:
    name: str
    score: int
    mode: str
    played_at: str


class Leaderboard:
    def __init__(self, path: Path | str, max_entries: int = 10) -> None:
        self.path = Path(path)
        self.max_entries = max_entries
        self.entries: list[LeaderboardEntry] = []
        self.load()

    def load(self) -> list[LeaderboardEntry]:
        if not self.path.exists():
            self.entries = []
            return self.entries

        with self.path.open("r", encoding="utf-8") as file:
            raw_entries = json.load(file)
        self.entries = [
            LeaderboardEntry(
                name=str(entry["name"]),
                score=int(entry["score"]),
                mode=str(entry.get("mode", "unknown")),
                played_at=str(entry.get("played_at", "")),
            )
            for entry in raw_entries
        ]
        self.entries.sort(key=lambda item: item.score, reverse=True)
        self.entries = self.entries[: self.max_entries]
        return self.entries

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump([asdict(entry) for entry in self.entries], file, ensure_ascii=False, indent=2)

    @property
    def top_score(self) -> int | None:
        if not self.entries:
            return None
        return self.entries[0].score

    def is_new_record(self, score: int) -> bool:
        top_score = self.top_score
        return top_score is None or score > top_score

    def add_entry(self, name: str, score: int, mode: str, played_at: str | None = None) -> LeaderboardEntry:
        timestamp = played_at or datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = LeaderboardEntry(name=name.strip() or "Игрок", score=score, mode=mode, played_at=timestamp)
        self.entries.append(entry)
        self.entries.sort(key=lambda item: item.score, reverse=True)
        self.entries = self.entries[: self.max_entries]
        self.save()
        return entry

