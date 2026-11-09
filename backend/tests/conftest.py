"""Configura una base de datos temporal ANTES de importar la app."""
import os
import tempfile

import pytest

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["STATIC_DIR"] = os.path.join(_tmp, "no-static")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:  # el "with" ejecuta el lifespan (crea tablas y coordinador)
        yield c


@pytest.fixture(scope="session")
def token_coord(client):
    r = client.post("/api/auth/login", json={"usuario": "coordinador", "clave": "coordinador123"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}
