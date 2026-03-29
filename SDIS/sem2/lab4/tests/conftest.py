from __future__ import annotations

import pytest

from app.services import PoliceSystem
from app.storage import PickleStorage


@pytest.fixture
def storage(tmp_path):
    return PickleStorage(data_dir=tmp_path)


@pytest.fixture
def service(storage):
    return PoliceSystem(storage=storage)


@pytest.fixture
def seeded_service(service):
    service.add_zone("Downtown")
    service.add_zone("Riverside")
    service.add_zone("OldTown")

    service.add_citizen("John Smith", zone="Downtown")
    service.add_citizen("Alice Brown", zone="Downtown")
    service.add_citizen("Mark Taylor", zone="Riverside")
    service.add_citizen("Emily Davis", zone="OldTown")

    service.hire_policeman("Miller", "Downtown")
    service.hire_policeman("Moore", "Downtown")
    service.hire_policeman("Clark", "Riverside")

    service.add_law(404, 4, "Fraud")
    service.create_statement("Bike theft", "Downtown", 0, 1)
    service.create_statement("Vandalism", "Riverside", 2, 0)
    service.save_data()
    return service
