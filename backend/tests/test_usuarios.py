"""Gestión de docentes, claves, edición de secciones y fecha según la zona horaria."""
from app.config import hoy


def _login(client, usuario, clave):
    r = client.post("/api/auth/login", json={"usuario": usuario, "clave": clave})
    return r.status_code, ({"Authorization": f"Bearer {r.json()['token']}"} if r.status_code == 200 else None)


def test_cambiar_mi_clave(client, token_coord):
    client.post("/api/docentes", headers=token_coord,
                json={"usuario": "doc_clave", "nombre": "Docente Clave", "clave": "inicial1"})
    _, h = _login(client, "doc_clave", "inicial1")
    r = client.put("/api/auth/clave", headers=h, json={"clave_actual": "mala", "clave_nueva": "nueva123"})
    assert r.status_code == 400
    r = client.put("/api/auth/clave", headers=h, json={"clave_actual": "inicial1", "clave_nueva": "nueva123"})
    assert r.status_code == 204
    assert _login(client, "doc_clave", "inicial1")[0] == 401
    assert _login(client, "doc_clave", "nueva123")[0] == 200


def test_coordinador_reinicia_clave_y_edita_nombre(client, token_coord):
    d = client.post("/api/docentes", headers=token_coord,
                    json={"usuario": "olvido", "nombre": "Olvidadizo", "clave": "secreta1"}).json()
    r = client.put(f"/api/docentes/{d['id']}", headers=token_coord, json={"nombre": "Prof. Olvidadizo", "clave": None})
    assert r.json()["nombre"] == "Prof. Olvidadizo"
    assert _login(client, "olvido", "secreta1")[0] == 200  # sin clave: no cambia
    client.put(f"/api/docentes/{d['id']}", headers=token_coord, json={"nombre": "Prof. Olvidadizo", "clave": "reinicio1"})
    assert _login(client, "olvido", "reinicio1")[0] == 200


def test_eliminar_docente_deja_seccion_sin_asignar(client, token_coord):
    d = client.post("/api/docentes", headers=token_coord,
                    json={"usuario": "temporal", "nombre": "Temporal", "clave": "secreta1"}).json()
    s = client.post("/api/secciones", headers=token_coord,
                    json={"codigo": "TMP1", "asignatura": "Temporal", "docente_id": d["id"]}).json()
    assert client.delete(f"/api/docentes/{d['id']}", headers=token_coord).status_code == 204
    assert client.get(f"/api/secciones/{s['id']}", headers=token_coord).json()["docente"] is None


def test_alcance_solo_docentes(client, token_coord):
    """El coordinador gestiona docentes, no coordinadores (fuera del alcance del MVP)."""
    # Aunque se envíe "rol", el usuario creado es siempre docente.
    d = client.post("/api/docentes", headers=token_coord, json={
        "usuario": "intento", "nombre": "Intento Coord", "clave": "secreta1", "rol": "coordinador"}).json()
    assert d["rol"] == "docente"
    # Las rutas de docentes no sirven para editar ni eliminar al coordinador.
    yo = client.get("/api/auth/yo", headers=token_coord).json()
    assert client.put(f"/api/docentes/{yo['id']}", headers=token_coord,
                      json={"nombre": "Otro", "clave": "hackeo12"}).status_code == 404
    assert client.delete(f"/api/docentes/{yo['id']}", headers=token_coord).status_code == 404
    # Un docente no puede gestionar docentes.
    _, hd = _login(client, "intento", "secreta1")
    assert client.get("/api/docentes", headers=hd).status_code == 403


def test_editar_seccion_conserva_asistencias(client, token_coord):
    d = client.post("/api/docentes", headers=token_coord,
                    json={"usuario": "nuevo_doc", "nombre": "Nuevo Docente", "clave": "secreta1"}).json()
    s = client.post("/api/secciones", headers=token_coord, json={"codigo": "ED-1", "asignatura": "Química"}).json()
    clase = client.post(f"/api/secciones/{s['id']}/clases", headers=token_coord, json={}).json()
    assert clase["fecha"] == hoy().isoformat()  # la fecha sale de la zona horaria configurada

    r = client.put(f"/api/secciones/{s['id']}", headers=token_coord,
                   json={"codigo": "ed-2", "asignatura": "Química General", "docente_id": d["id"]})
    assert r.json()["codigo"] == "ED-2" and r.json()["docente"]["id"] == d["id"]
    assert len(client.get(f"/api/secciones/{s['id']}/clases", headers=token_coord).json()) == 1
    # El nuevo docente ahora ve la sección.
    _, hd = _login(client, "nuevo_doc", "secreta1")
    assert [x["codigo"] for x in client.get("/api/secciones", headers=hd).json()] == ["ED-2"]
