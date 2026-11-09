"""Prueba de punta a punta del flujo principal a través de la API."""
from app.routers.clases import generador_qr
from app.database import SessionLocal
from app.models import Clase


def test_flujo_completo(client, token_coord):
    # 1. El coordinador crea un docente y una sección asignada a él.
    r = client.post("/api/docentes", headers=token_coord,
                    json={"usuario": "prof", "nombre": "Prof. Ramírez", "clave": "secreta1"})
    assert r.status_code == 201
    docente_id = r.json()["id"]
    r = client.post("/api/secciones", headers=token_coord,
                    json={"codigo": "prog3-a", "asignatura": "Programación III", "docente_id": docente_id})
    assert r.status_code == 201 and r.json()["codigo"] == "PROG3-A"
    seccion_id = r.json()["id"]

    # 2. Carga la matrícula.
    csv = "nombres,apellidos,cedula\nAna,Pérez,111\nLuis,Gómez,222\nEva,Díaz,333\nJuan,Ruiz,444\n"
    r = client.post(f"/api/secciones/{seccion_id}/matricula", headers=token_coord,
                    files={"archivo": ("m.csv", csv.encode(), "text/csv")})
    assert r.json() == {"agregados": 4, "ya_inscritos": 0, "errores": []}

    # 3. El docente inicia sesión y abre una clase.
    r = client.post("/api/auth/login", json={"usuario": "prof", "clave": "secreta1"})
    doc = {"Authorization": f"Bearer {r.json()['token']}"}
    assert [s["id"] for s in client.get("/api/secciones", headers=doc).json()] == [seccion_id]
    clase_id = client.post(f"/api/secciones/{seccion_id}/clases", headers=doc, json={"tema": "POO"}).json()["id"]
    codigo = client.get(f"/api/clases/{clase_id}/qr", headers=doc).json()["codigo"]

    # 4. Los alumnos escanean y marcan.
    assert client.get(f"/api/publico/clases/{clase_id}?c={codigo}").json()["codigo_valido"]
    for cedula in ("111", "V-222", "333"):
        r = client.post("/api/publico/asistencia", json={"clase_id": clase_id, "codigo": codigo, "cedula": cedula})
        assert r.status_code == 200, r.text
    r = client.post("/api/publico/asistencia", json={"clase_id": clase_id, "codigo": codigo, "cedula": "111"})
    assert "Ya tenías" in r.json()["mensaje"]
    r = client.post("/api/publico/asistencia", json={"clase_id": clase_id, "codigo": codigo, "cedula": "9999"})
    assert r.status_code == 404
    r = client.post("/api/publico/asistencia", json={"clase_id": clase_id, "codigo": "malo123", "cedula": "444"})
    assert r.status_code == 400

    # 5. Segunda clase: solo asiste Ana. Se cierra y ya no acepta marcajes.
    clase2 = client.post(f"/api/secciones/{seccion_id}/clases", headers=doc, json={}).json()["id"]
    with SessionLocal() as db:
        c2 = db.get(Clase, clase2)
        cod2 = generador_qr.generar(c2.secreto, c2.id)
    client.post("/api/publico/asistencia", json={"clase_id": clase2, "codigo": cod2, "cedula": "111"})
    client.post(f"/api/clases/{clase2}/cerrar", headers=doc)
    r = client.post("/api/publico/asistencia", json={"clase_id": clase2, "codigo": cod2, "cedula": "222"})
    assert r.status_code == 400

    # 6. Estadísticas: 4 alumnos x 2 clases = 8 cupos, 4 asistencias → 50 %.
    est = client.get(f"/api/secciones/{seccion_id}/estadisticas", headers=doc).json()
    assert est["resumen"]["promedio_asistencia"] == 50.0
    por_cedula = {e["cedula"]: e for e in est["estudiantes"]}
    assert por_cedula["111"]["porcentaje"] == 100.0
    assert por_cedula["222"]["porcentaje"] == 50.0 and por_cedula["222"]["en_riesgo"]
    assert por_cedula["444"]["asistencias"] == 0
    assert est["resumen"]["estudiantes_en_riesgo"] == 3

    gen = client.get("/api/estadisticas/general", headers=token_coord).json()
    assert gen["total_secciones"] == 1 and gen["promedio_asistencia"] == 50.0
    assert client.get("/api/estadisticas/general", headers=doc).status_code == 403

    # 7. Reportes.
    pdf = client.get(f"/api/secciones/{seccion_id}/reporte?formato=pdf", headers=doc)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    xlsx = client.get(f"/api/secciones/{seccion_id}/reporte?formato=excel", headers=doc)
    assert xlsx.status_code == 200 and xlsx.content.startswith(b"PK")

    # 8. Pase de lista manual.
    r = client.put(f"/api/clases/{clase_id}/asistentes/{por_cedula['444']['estudiante_id']}", headers=doc)
    assert r.json()["presente"] is True


def test_sin_token_no_hay_acceso(client):
    assert client.get("/api/secciones").status_code == 401
