from __future__ import annotations

from pathlib import Path

import main
import scripts.generate_demo_data as generate_demo_data
from app.repositories import TournamentRepository


def test_build_records_creates_meaningful_unique_records():
    records = generate_demo_data.build_records(batch_index=2, count=10)

    assert len(records) == 10
    assert len({record.tournament_name for record in records}) == 10
    assert all(record.winner_earnings == round(record.prize_amount * 0.6, 2) for record in records)


def test_create_demo_files_writes_expected_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(generate_demo_data, "ROOT_DIR", tmp_path)
    generate_demo_data.create_demo_files()

    data_dir = tmp_path / "data"
    assert (data_dir / "demo_batch_1.xml").exists()
    assert (data_dir / "demo_batch_2.xml").exists()
    assert (data_dir / "demo_batch_1.db").exists()
    assert (data_dir / "demo_batch_2.db").exists()
    assert (data_dir / "tournaments.db").exists()

    repository = TournamentRepository(data_dir / "tournaments.db")
    try:
        assert repository.count_records() == 120
    finally:
        repository.close()


def test_main_function_creates_window_and_returns_exit_code(tmp_path, monkeypatch):
    created = {"controller_path": None, "shown": False, "app_name": None}

    class FakeApplication:
        def __init__(self, argv):
            self.argv = argv

        def setApplicationName(self, name):
            created["app_name"] = name

        def exec_(self):
            return 77

    class FakeController:
        def __init__(self, database_path):
            created["controller_path"] = database_path

    class FakeWindow:
        def __init__(self, controller):
            self.controller = controller

        def show(self):
            created["shown"] = True

    fake_main_path = tmp_path / "project" / "main.py"
    fake_main_path.parent.mkdir(parents=True, exist_ok=True)
    fake_main_path.write_text("# fake main", encoding="utf-8")

    monkeypatch.setattr(main, "__file__", str(fake_main_path))
    monkeypatch.setattr(main, "QApplication", FakeApplication)
    monkeypatch.setattr(main, "AppController", FakeController)
    monkeypatch.setattr(main, "MainWindow", FakeWindow)

    exit_code = main.main()

    assert exit_code == 77
    assert created["app_name"] == "Каталог турниров"
    assert created["controller_path"] == Path(fake_main_path).resolve().parent / "data" / "tournaments.db"
    assert created["shown"] is True
