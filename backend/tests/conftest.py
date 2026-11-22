"""Configura una base de datos temporal ANTES de importar la app.

Por defecto usa SQLite en una carpeta temporal. Para probar contra PostgreSQL
(lo mismo que Supabase), definir TEST_DATABASE_URL, p. ej.:
    TEST_DATABASE_URL=postgresql://postgres:test@localhost:55432/postgres
¡Ojo! Esa base se VACÍA al empezar. Nunca apuntarla a la base de producción.
"""
import os
import tempfile

import pytest

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", f"sqlite:///{_tmp}/test.db")
os.environ["STATIC_DIR"] = os.path.join(_tmp, "no-static")

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    Base.metadata.drop_all(engine)  # empezar siempre de cero
    with TestClient(app) as c:  # el "with" ejecuta el lifespan (crea tablas y coordinador)
        yield c


@pytest.fixture(scope="session")
def token_coord(client):
    r = client.post("/api/auth/login", json={"usuario": "coordinador", "clave": "coordinador123"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}
