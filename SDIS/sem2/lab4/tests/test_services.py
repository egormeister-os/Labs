from __future__ import annotations

import importlib

from app.domain import Citizen, Crime, Law, Policeman
from app.services import PoliceSystem
from app.storage import PickleStorage


def test_service_defaults_and_dashboard(service):
    state = service.get_dashboard_state()
    assert state.zones_count == 0
    assert state.laws_count >= 3
    assert state.crimes_count == 0


def test_add_zone_and_duplicate(service):
    result = service.add_zone("Downtown")
    assert result.ok is True
    duplicate = service.add_zone("Downtown")
    assert duplicate.ok is False


def test_citizen_operations(service):
    service.add_zone("Downtown")
    bad = service.add_citizen("John", zone="Missing")
    assert bad.ok is False

    created = service.add_citizen("John Smith", zone="Downtown")
    assert created.ok is True
    assert len(service.list_citizens()) == 1

    deleted = service.delete_citizen(0)
    assert deleted.ok is True
    assert service.delete_citizen(0).ok is False
    assert service.delete_citizen(-1).ok is False


def test_statement_branches(service):
    assert service.create_statement("Test", "Downtown", 0, 0).ok is False
    service.add_zone("Downtown")
    service.add_citizen("John Smith", zone="Downtown")

    original_laws = service.laws
    service.laws = []
    assert service.create_statement("Test", "Downtown", 0, 0).ok is False
    service.laws = original_laws

    assert service.create_statement("Test", "Missing", 0, 0).ok is False
    assert service.create_statement("Test", "Downtown", -1, 0).ok is False
    assert service.create_statement("Test", "Downtown", 99, 0).ok is False

    created = service.create_statement("Bike theft", "Downtown", 0, 0)
    assert created.ok is True
    assert len(service.list_statements()) == 1
    assert service.delete_statement(-1).ok is False
    assert service.delete_statement(50).ok is False
    assert service.delete_statement(0).ok is True


def test_police_operations(service):
    assert service.hire_policeman("Miller", "Downtown").ok is False
    service.add_zone("Downtown")
    assert service.hire_policeman("Miller", "Downtown").ok is True
    assert len(service.list_policemen()) == 1
    assert service.fire_policeman("Unknown").ok is False
    assert service.fire_policeman("Miller").ok is True


def test_recover_and_zone_info(service):
    service.add_zone("Downtown")
    service.hire_policeman("Miller", "Downtown")
    officer = service.list_policemen()[0]
    officer._fatigue = 6
    officer.check_exhaustion()

    result = service.recover_policemen()
    assert result.ok is True
    assert "recovered" in result.message
    assert service.recover_policemen().message == "No officers need recovery"

    zone_info = service.get_zone_info()
    assert zone_info[0]["zone"] == "Downtown"
    assert zone_info[0]["officers"][0]["fatigue_status"] == "Fresh"


def test_relocate_branches(service):
    service.add_zone("Downtown")
    service.add_zone("Riverside")
    service.hire_policeman("Miller", "Downtown")

    assert service.relocate_policemen([0], "Missing").ok is False
    assert service.relocate_policemen([-1], "Riverside").ok is False
    assert service.relocate_policemen([999], "Riverside").ok is False

    moved = service.relocate_policemen([0], "Riverside")
    assert moved.ok is True
    assert service.list_policemen()[0].zone == "Riverside"


def test_investigation_and_arrests(service):
    service.add_zone("Downtown")
    service.add_citizen("John Smith", zone="Downtown")
    service.hire_policeman("Miller", "Downtown")
    service.create_statement("Bike theft", "Downtown", 0, 0)

    investigation_module = importlib.import_module("app.domain.Investigation")
    original_random = investigation_module.random.random
    investigation_module.random.random = lambda: 0.0
    try:
        result = service.investigate_crimes()
    finally:
        investigation_module.random.random = original_random
    assert result.ok is True
    assert "Assigned to" in " ".join(result.details)

    policeman_module = importlib.import_module("app.domain.Policeman")
    original_policeman_random = policeman_module.random.random
    policeman_module.random.random = lambda: 0.0
    try:
        arrest_result = service.arrest_criminals()
    finally:
        policeman_module.random.random = original_policeman_random
    assert arrest_result.ok is True
    assert any("Successful" in detail for detail in arrest_result.details)


def test_investigation_failure_branches(service):
    assert service.investigate_crimes().ok is False

    service.add_zone("Downtown")
    service.add_citizen("John Smith", zone="Downtown")
    service.hire_policeman("Miller", "Downtown")
    service.create_statement("Bike theft", "Downtown", 0, 0)

    investigation_module = importlib.import_module("app.domain.Investigation")
    original_random = investigation_module.random.random
    investigation_module.random.random = lambda: 0.99
    try:
        result = service.investigate_crimes()
    finally:
        investigation_module.random.random = original_random
    assert result.ok is False


def test_investigation_with_arrest_option(service):
    service.add_zone("Downtown")
    service.add_citizen("John Smith", zone="Downtown")
    service.hire_policeman("Miller", "Downtown")
    service.create_statement("Bike theft", "Downtown", 0, 0)

    investigation_module = importlib.import_module("app.domain.Investigation")
    policeman_module = importlib.import_module("app.domain.Policeman")
    original_investigation = investigation_module.random.random
    original_policeman = policeman_module.random.random
    investigation_module.random.random = lambda: 0.0
    policeman_module.random.random = lambda: 0.0
    try:
        result = service.investigate_crimes(do_arrest=True)
    finally:
        investigation_module.random.random = original_investigation
        policeman_module.random.random = original_policeman
    assert result.ok is True
    assert "Arrest processing completed" in result.details[-1]


def test_history_laws_and_save_load(service, tmp_path):
    service.add_zone("Downtown")
    service.add_citizen("John Smith", zone="Downtown")
    assert service.list_history()
    assert service.clear_history().ok is True
    assert service.list_history() == []

    created = service.add_law(700, 5, "Serious fraud")
    assert created.ok is True
    assert any(law.article == 700 for law in service.list_laws())

    saved = service.save_data()
    assert saved.ok is True

    loaded = PoliceSystem(storage=PickleStorage(data_dir=tmp_path))
    assert any(law.article == 700 for law in loaded.list_laws())
