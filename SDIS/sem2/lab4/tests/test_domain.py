from __future__ import annotations

import importlib

import pytest

from app.domain import Citizen, Crime, Law, Police, Policeman, Security, ZoneNotFoundError


def test_citizen_validation_and_repr():
    citizen = Citizen("John Doe", zone="Downtown")
    assert citizen.name == "John Doe"
    assert citizen.zone == "Downtown"
    assert "Downtown" in repr(citizen)
    assert "John Doe" in str(citizen)

    citizen.name = "Jane Doe"
    citizen.zone = "Riverside"
    assert citizen.name == "Jane Doe"
    assert citizen.zone == "Riverside"


@pytest.mark.parametrize("bad_name", ["", " ", "A"])
def test_citizen_rejects_invalid_names(bad_name):
    with pytest.raises(ValueError):
        Citizen(bad_name)


def test_citizen_rejects_non_string_name():
    with pytest.raises(TypeError):
        Citizen(123)  # type: ignore[arg-type]


def test_citizen_submit_application():
    suspect = Citizen("Suspect Name", zone="Downtown")
    reporter = Citizen("Reporter Name", zone="Downtown")
    law = Law(101, severity=3, desc="Theft")

    crime = reporter.submit_application(suspect, "Stole a bag", "Downtown", law)

    assert isinstance(crime, Crime)
    assert crime.suspect is suspect
    assert crime.severity == 3


def test_crime_equality_hash_and_string():
    suspect = Citizen("Alex Stone")
    law = Law(202, severity=2, desc="Damage")
    crime1 = Crime(suspect, "Broken window", "Center", law)
    crime2 = Crime(suspect, "Broken window", "Center", law)

    assert crime1 == crime2
    assert hash(crime1) == hash(crime2)
    assert "Broken window" in str(crime1)
    assert "Crime" in repr(crime1)


def test_law_validation_and_repr():
    law = Law(500, severity=5, desc="Serious crime")
    law.desc = "Updated"
    law.severity = 4
    assert law.article == 500
    assert law.desc == "Updated"
    assert law.severity == 4
    assert "500" in repr(law)

    with pytest.raises(ValueError):
        Law(100, severity=6)
    with pytest.raises(TypeError):
        law.severity = "bad"  # type: ignore[assignment]
    with pytest.raises(ValueError):
        law.severity = 0


def test_police_core_operations():
    police = Police()
    police.create_zone("Downtown")
    assert police.has_zone("Downtown")

    officer = Policeman("Miller", "Downtown")
    police.hire(officer, "Downtown")
    assert police.get_policemen() == [officer]
    assert police.get_policemen_by_zone("Downtown") == [officer]

    police.create_zone("Riverside")
    police.relocate([officer], "Riverside")
    assert officer.zone == "Riverside"
    assert police.get_policemen_by_zone("Riverside") == [officer]

    suspect = Citizen("John Smith", zone="Riverside")
    law = Law(111, severity=1, desc="Minor offense")
    crime = Crime(suspect, "Noise", "Riverside", law)
    assert police.get_crimes_by_zone("Riverside", [crime]) == [crime]
    assert police.get_all_crimes([crime]) == [crime]

    police.update_zone_security("Riverside", citizen_count=5, crime_count=1)
    assert police.zones["Riverside"]["security"] == 5.0
    police.update_zone_security("Downtown", citizen_count=0, crime_count=1)
    assert police.zones["Downtown"]["security"] == 0.0

    police.fire(officer)
    assert officer.is_work is False


def test_police_errors():
    police = Police()
    police.create_zone("Downtown")
    with pytest.raises(Exception):
        police.create_zone("Downtown")
    with pytest.raises(ZoneNotFoundError):
        police.get_policemen_by_zone("Missing")


def test_policeman_behaviour():
    suspect = Citizen("Suspect Person")
    law = Law(301, severity=5, desc="Violent crime")
    crime = Crime(suspect, "Assault", "Downtown", law)
    officer = Policeman("Moore", "Downtown")
    officer.assign_crime((crime, law.severity))
    assert officer.has_assignment is True
    assert officer.assignment is not None

    policeman_module = importlib.import_module("app.domain.Policeman")
    original = policeman_module.random.random
    policeman_module.random.random = lambda: 0.0
    try:
        assert officer.arrest() is True
    finally:
        policeman_module.random.random = original

    assert officer.has_assignment is False
    assert officer.arrest() is False

    officer.assign_crime((crime, law.severity))
    officer._fatigue = 5
    policeman_module.random.random = lambda: 0.99
    try:
        assert officer.arrest() is False
    finally:
        policeman_module.random.random = original
    assert officer.is_resting is True

    officer.recovery()
    assert officer.is_resting is False
    assert officer.fatigue == 0

    officer.lastname = "Updated"
    officer.zone = "Riverside"
    officer.is_work = False
    officer.clear_assignment()
    assert "Updated" in repr(officer)
    assert "Riverside" in str(officer)

    with pytest.raises(ValueError):
        Policeman("", "Downtown")
    with pytest.raises(TypeError):
        officer.lastname = 12  # type: ignore[assignment]


def test_investigation_paths():
    investigation_module = importlib.import_module("app.domain.Investigation")
    suspect = Citizen("Detected Person")
    law = Law(201, severity=3, desc="Theft")
    crime = Crime(suspect, "Stole phone", "Center", law)
    investigation = investigation_module.Investigation([crime])

    original = investigation_module.random.random
    investigation_module.random.random = lambda: 0.0
    try:
        result = investigation.investigate()
        results = investigation.investigate_all()
    finally:
        investigation_module.random.random = original

    assert result == (crime, 3)
    assert results == [(crime, 3)]
    assert investigation.crimes == [crime]
    assert "1" in repr(investigation)


def test_security_branches():
    security = Security()
    assert security.eval([], []) == 10.0

    law = Law(101, severity=1, desc="Minor")
    suspect = Citizen("John Snow")
    crime = Crime(suspect, "Minor", "OldTown", law)
    assert security.eval([], [crime]) == 0.0
    assert security.eval([suspect], [crime]) == 1.0

    security.decrease(0.5)
    assert security.level == 0.5
    security.increase(1.5)
    assert security.level == 2.0
    assert "Medium" in str(security)

    with pytest.raises(ValueError):
        security.level = -1
