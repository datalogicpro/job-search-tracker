import pytest
from django.db import DatabaseError


class BrokenConnection:
    def cursor(self):
        raise DatabaseError("database is down")


@pytest.mark.django_db
def test_health_ok_when_database_answers(client):
    response = client.get("/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_503_when_database_is_down(client, monkeypatch):
    monkeypatch.setattr("config.health.connection", BrokenConnection())

    response = client.get("/health/")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}


def test_health_refuses_post(client):
    response = client.post("/health/")

    assert response.status_code == 405