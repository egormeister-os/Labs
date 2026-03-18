from __future__ import annotations

import os
from datetime import date

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from app.controllers import AppController
from app.models import TournamentRecordInput
from app.repositories import TournamentRepository


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def make_input():
    def _make_input(
        tournament_name: str = "Кубок Минска",
        event_date: date = date(2025, 2, 10),
        sport_name: str = "Tennis",
        winner_full_name: str = "Иванов Иван Иванович",
        prize_amount: float = 1000.0,
    ) -> TournamentRecordInput:
        return TournamentRecordInput(
            tournament_name=tournament_name,
            event_date=event_date,
            sport_name=sport_name,
            winner_full_name=winner_full_name,
            prize_amount=prize_amount,
        )

    return _make_input


@pytest.fixture
def sample_inputs(make_input):
    return [
        make_input(
            tournament_name="Кубок Минска",
            event_date=date(2025, 1, 10),
            sport_name="Tennis",
            winner_full_name="Иванов Иван Иванович",
            prize_amount=1000.0,
        ),
        make_input(
            tournament_name="Открытый Брест",
            event_date=date(2025, 3, 1),
            sport_name="Football",
            winner_full_name="Петров Петр Петрович",
            prize_amount=3200.0,
        ),
        make_input(
            tournament_name="Зимний Кубок",
            event_date=date(2024, 12, 25),
            sport_name="Tennis",
            winner_full_name="Сидоров Алексей Сергеевич",
            prize_amount=2500.5,
        ),
    ]


@pytest.fixture
def sample_records(sample_inputs):
    return [record_input.to_record(record_id=index + 1) for index, record_input in enumerate(sample_inputs)]


@pytest.fixture
def repository(tmp_path, sample_inputs):
    repo = TournamentRepository(tmp_path / "test.db")
    for record_input in sample_inputs:
        repo.add_record(record_input)
    yield repo
    repo.close()


@pytest.fixture
def controller(tmp_path, sample_inputs):
    app_controller = AppController(tmp_path / "controller.db")
    for record_input in sample_inputs:
        app_controller.add_record(record_input)
    yield app_controller
    app_controller.close()
