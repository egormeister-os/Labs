from __future__ import annotations

import importlib

import pytest

from app import create_app
from app.services import PoliceSystem


@pytest.fixture
def client(storage, monkeypatch):
    routes = importlib.import_module("app.web.routes")

    def factory():
        return PoliceSystem(storage=storage)

    monkeypatch.setattr(routes, "get_service", factory)
    app = create_app()
    app.config.update(TESTING=True, SECRET_KEY="test-secret")
    return app.test_client()


def test_all_get_pages_render(client):
    for path in ["/", "/citizens", "/police", "/statements", "/laws", "/investigation", "/history"]:
        response = client.get(path)
        assert response.status_code == 200


def test_citizen_routes(client):
    client.post("/zones", data={"zone": "Downtown", "next": "/police"})
    response = client.post("/citizens", data={"name": "John Smith", "zone": "Downtown", "next": "/citizens"})
    assert response.status_code == 302

    response = client.post("/citizens/0/delete", data={"next": "/citizens"})
    assert response.status_code == 302


def test_police_routes(client):
    client.post("/zones", data={"zone": "Downtown", "next": "/police"})
    client.post("/zones", data={"zone": "Riverside", "next": "/police"})

    response = client.post("/policemen", data={"lastname": "Miller", "zone": "Downtown", "next": "/police"})
    assert response.status_code == 302

    response = client.post("/policemen/fire", data={"lastname": "Unknown", "next": "/police"})
    assert response.status_code == 302

    client.post("/policemen", data={"lastname": "Moore", "zone": "Downtown", "next": "/police"})
    response = client.post(
        "/policemen/relocate",
        data={"indexes": "0 1", "target_zone": "Riverside", "next": "/police"},
    )
    assert response.status_code == 302

    response = client.post(
        "/policemen/relocate",
        data={"indexes": "bad", "target_zone": "Riverside", "next": "/police"},
    )
    assert response.status_code == 302

    response = client.post("/policemen/recover", data={"next": "/police"})
    assert response.status_code == 302


def test_statement_routes(client):
    client.post("/zones", data={"zone": "Downtown", "next": "/police"})
    client.post("/citizens", data={"name": "John Smith", "zone": "Downtown", "next": "/citizens"})

    response = client.post(
        "/statements",
        data={
            "description": "Bike theft",
            "zone": "Downtown",
            "suspect_idx": "0",
            "law_idx": "0",
            "next": "/statements",
        },
    )
    assert response.status_code == 302

    response = client.post(
        "/statements",
        data={
            "description": "Bad indexes",
            "zone": "Downtown",
            "suspect_idx": "x",
            "law_idx": "0",
            "next": "/statements",
        },
    )
    assert response.status_code == 302

    response = client.post("/statements/0/delete", data={"next": "/statements"})
    assert response.status_code == 302


def test_law_routes(client):
    response = client.post("/laws", data={"article": "404", "severity": "4", "desc": "Fraud", "next": "/laws"})
    assert response.status_code == 302

    response = client.post("/laws", data={"article": "x", "severity": "4", "desc": "Fraud", "next": "/laws"})
    assert response.status_code == 302


def test_investigation_and_history_routes(client, storage):
    service = PoliceSystem(storage=storage)
    service.add_zone("Downtown")
    service.add_citizen("John Smith", zone="Downtown")
    service.hire_policeman("Miller", "Downtown")
    service.create_statement("Bike theft", "Downtown", 0, 0)
    service.save_data()

    investigation_module = importlib.import_module("app.domain.Investigation")
    policeman_module = importlib.import_module("app.domain.Policeman")
    original_investigation = investigation_module.random.random
    original_policeman = policeman_module.random.random
    investigation_module.random.random = lambda: 0.0
    policeman_module.random.random = lambda: 0.0
    try:
        response = client.post("/investigation", data={"mode": "investigate", "next": "/investigation"})
        assert response.status_code == 302
        response = client.post(
            "/investigation",
            data={"mode": "investigate_and_arrest", "next": "/investigation"},
        )
        assert response.status_code == 302
        response = client.post("/arrests", data={"next": "/investigation"})
        assert response.status_code == 302
    finally:
        investigation_module.random.random = original_investigation
        policeman_module.random.random = original_policeman

    response = client.post("/history/clear", data={"next": "/history"})
    assert response.status_code == 302
