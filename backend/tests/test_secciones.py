"""Una sección con varias asignaturas, matrícula sin duplicados y migración de bases viejas."""
import os

from sqlalchemy import create_engine, inspect, text


def _csv(*filas):
    return ("nombres,apellidos,cedula\n" + "\n".join(filas) + "\n").encode()


def test_varias_asignaturas_por_seccion(client, token_coord):
    a = client.post("/api/secciones", headers=token_coord, json={"codigo": "n700", "asignatura": "Bases de Datos I"})
    b = client.post("/api/secciones", headers=token_coord, json={"codigo": "N700", "asignatura": "Programación III"})
    assert a.status_code == 201 and b.status_code == 201
    assert a.json()["codigo"] == b.json()["codigo"] == "N700"

    # La misma asignatura dos veces en la misma sección no (ignora mayúsculas).
    r = client.post("/api/secciones", headers=token_coord, json={"codigo": "N700", "asignatura": "programación iii"})
    assert r.status_code == 409 and "Programación III" in r.json()["detail"]

    # Editar una para que choque con la otra tampoco.
    r = client.put(f"/api/secciones/{a.json()['id']}", headers=token_coord,
                   json={"codigo": "N700", "asignatura": "Programación III", "docente_id": None})
    assert r.status_code == 409
    # Pero editarla sin cambiar nada sí.
    r = client.put(f"/api/secciones/{a.json()['id']}", headers=token_coord,
                   json={"codigo": "N700", "asignatura": "Bases de Datos I", "docente_id": None})
    assert r.status_code == 200

    # El nombre del reporte distingue la asignatura.
    d = client.post("/api/docentes", headers=token_coord,
                    json={"usuario": "doc_n700", "nombre": "Doc N700", "clave": "secreta1"}).json()
    client.put(f"/api/secciones/{b.json()['id']}", headers=token_coord,
               json={"codigo": "N700", "asignatura": "Programación III", "docente_id": d["id"]})
    r = client.get(f"/api/secciones/{b.json()['id']}/reporte?formato=excel", headers=token_coord)
    assert "asistencia_N700_programacion-iii_" in r.headers["content-disposition"]


def test_matricula_cuenta_alumnos_distintos(client, token_coord):
    antes = client.get("/api/estadisticas/general", headers=token_coord).json()
    s1 = client.post("/api/secciones", headers=token_coord, json={"codigo": "M1", "asignatura": "Física"}).json()
    s2 = client.post("/api/secciones", headers=token_coord, json={"codigo": "M1", "asignatura": "Química"}).json()
    s3 = client.post("/api/secciones", headers=token_coord, json={"codigo": "M2", "asignatura": "Física"}).json()
    # 91000001 está en las tres; 91000002 en dos; 91000003 solo en una → 3 alumnos, 6 inscripciones.
    for s, archivo in [(s1, _csv("Ana,Uno,91000001", "Beto,Dos,91000002")),
                       (s2, _csv("Ana,Uno,91000001", "Carla,Tres,91000003")),
                       (s3, _csv("Ana,Uno,91000001", "Beto,Dos,91000002"))]:
        client.post(f"/api/secciones/{s['id']}/matricula", headers=token_coord,
                    files={"archivo": ("m.csv", archivo, "text/csv")})

    despues = client.get("/api/estadisticas/general", headers=token_coord).json()
    assert despues["matricula"] - antes["matricula"] == 3
    assert despues["total_asignaturas"] - antes["total_asignaturas"] == 3
    assert despues["total_secciones"] - antes["total_secciones"] == 2  # M1 y M2


def test_migra_base_vieja_con_codigo_unico(tmp_path):
    """Una base creada con la versión anterior (código ÚNICO) queda migrada al arrancar."""
    from app import main

    url = os.environ.get("TEST_DATABASE_URL")
    if url:  # PostgreSQL: usar un esquema aparte para no tocar las tablas de las otras pruebas
        url = "postgresql+psycopg://" + url.split("://", 1)[1]
        motor = create_engine(url, connect_args={"options": "-c search_path=migracion"})
        with motor.begin() as con:
            con.execute(text("DROP SCHEMA IF EXISTS migracion CASCADE; CREATE SCHEMA migracion"))
    else:
        motor = create_engine(f"sqlite:///{tmp_path / 'vieja.db'}")

    with motor.begin() as con:  # esquema tal como lo creaba la versión anterior
        con.execute(text("CREATE TABLE secciones (id INTEGER PRIMARY KEY, codigo VARCHAR(20) NOT NULL, "
                         "asignatura VARCHAR(120) NOT NULL)"))
        con.execute(text("CREATE UNIQUE INDEX ix_secciones_codigo ON secciones (codigo)"))
        con.execute(text("INSERT INTO secciones VALUES (1, 'N613', 'Calidad y Productividad')"))

    original = main.engine
    main.engine = motor
    try:
        main._migrar_codigo_de_seccion()
        main._migrar_codigo_de_seccion()  # idempotente: la segunda vez no hace nada
    finally:
        main.engine = original

    indices = {i["name"]: i for i in inspect(motor).get_indexes("secciones")}
    assert not indices["ix_secciones_codigo"]["unique"]
    assert indices["uq_seccion_codigo_asignatura"]["unique"]
    with motor.begin() as con:
        con.execute(text("INSERT INTO secciones VALUES (2, 'N613', 'Programación III')"))  # ahora sí se puede
        assert con.execute(text("SELECT count(*) FROM secciones")).scalar() == 2
    if url:
        with motor.begin() as con:
            con.execute(text("DROP SCHEMA migracion CASCADE"))
    motor.dispose()
