"""Regression tests for CLI system behavior in main.py."""

from __future__ import annotations

import pytest

import main
from police import Citizen, Crime, Law, Police, Policeman


@pytest.fixture
def isolated_system(monkeypatch: pytest.MonkeyPatch, tmp_path) -> main.PoliceSystem:
    """Create a PoliceSystem instance that stores data only in tmp_path."""
    monkeypatch.setattr(main, "DATA_DIR", tmp_path / "data")
    system = main.PoliceSystem()
    system.police = Police()
    system.applications = []
    system.history = []
    system.citizens = []
    system.laws = [Law(101, severity=1, desc="Minor offense")]
    return system


def test_arrest_cleanup_removes_only_solved_crime(
    isolated_system: main.PoliceSystem,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    isolated_system.police.add_zone("A")
    law = isolated_system.laws[0]
    suspect_one = Citizen("Alex")
    suspect_two = Citizen("Alex")
    crime_one = Crime(suspect=suspect_one, description="Case #1", zone="A", law=law)
    crime_two = Crime(suspect=suspect_two, description="Case #2", zone="A", law=law)
    isolated_system.applications = [crime_one, crime_two]

    officer = Policeman(lastname="Smith", zone="A")
    isolated_system.police.hire(officer, "A")
    officer.assign_crime((crime_one, crime_one.severity))

    monkeypatch.setattr(officer, "arrest", lambda: True)

    isolated_system._perform_arrests_and_cleanup()

    assert isolated_system.applications == [crime_two]


def test_create_statement_rejects_negative_indexes(
    isolated_system: main.PoliceSystem,
    capsys: pytest.CaptureFixture[str],
) -> None:
    isolated_system.police.add_zone("A")
    isolated_system.citizens = [Citizen("John"), Citizen("Mary")]

    isolated_system.create_statement("Test", "A", -1, 0)
    out = capsys.readouterr().out

    assert "Invalid citizen or law index" in out
    assert isolated_system.applications == []


def test_delete_statement_rejects_negative_index(
    isolated_system: main.PoliceSystem,
    capsys: pytest.CaptureFixture[str],
) -> None:
    isolated_system.police.add_zone("A")
    law = isolated_system.laws[0]
    suspect = Citizen("John")
    isolated_system.applications = [Crime(suspect, "Test", "A", law)]

    isolated_system.delete_statement(-1)
    out = capsys.readouterr().out

    assert "Invalid application index" in out
    assert len(isolated_system.applications) == 1


def test_delete_citizen_rejects_negative_index(
    isolated_system: main.PoliceSystem,
    capsys: pytest.CaptureFixture[str],
) -> None:
    isolated_system.citizens = [Citizen("John")]

    isolated_system.delete_citizen(-1)
    out = capsys.readouterr().out

    assert "Invalid citizen index" in out
    assert len(isolated_system.citizens) == 1


def test_relocate_rejects_negative_index(
    isolated_system: main.PoliceSystem,
    capsys: pytest.CaptureFixture[str],
) -> None:
    isolated_system.police.add_zone("A")
    isolated_system.police.add_zone("B")
    officer = Policeman(lastname="Smith", zone="A")
    isolated_system.police.hire(officer, "A")

    isolated_system.relocate_policemen([-1], "B")
    out = capsys.readouterr().out

    assert "Invalid policeman index" in out
    assert officer.zone == "A"


def test_parser_requires_subcommand() -> None:
    parser = main.create_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["citizen"])
