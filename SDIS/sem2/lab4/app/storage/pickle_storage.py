from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

from app.domain import Law, Police, Security


class PickleStorage:
    DATA_FILES = {
        "police": "police.pkl",
        "applications": "applications.pkl",
        "history": "history.pkl",
        "citizens": "citizens.pkl",
        "laws": "laws.pkl",
        "security": "security.pkl",
    }

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or Path("pickle_storage")
        self.data_dir.mkdir(exist_ok=True)

    def load(self) -> dict[str, Any]:
        defaults: dict[str, Any] = {
            "police": Police(),
            "applications": [],
            "history": [],
            "laws": [
                Law(101, severity=1, desc="Minor offense"),
                Law(201, severity=3, desc="Theft"),
                Law(301, severity=5, desc="Violent crime"),
            ],
            "security": Security(),
            "citizens": [],
        }

        state: dict[str, Any] = {}
        for key, filename in self.DATA_FILES.items():
            path = self.data_dir / filename
            try:
                with open(path, "rb") as file_obj:
                    state[key] = pickle.load(file_obj)
            except (FileNotFoundError, EOFError, pickle.UnpicklingError):
                state[key] = defaults[key]
        return state

    def save(self, state: dict[str, Any]) -> None:
        for key, filename in self.DATA_FILES.items():
            path = self.data_dir / filename
            with open(path, "wb") as file_obj:
                pickle.dump(state[key], file_obj)
