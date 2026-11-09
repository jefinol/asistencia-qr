"""Pruebas unitarias de la lógica pura (sin base de datos ni HTTP)."""
from app.services.codigo_qr import GeneradorCodigoQR
from app.services.matricula import LectorMatricula


def test_codigo_qr_rota_y_tolera_ventana_anterior():
    g = GeneradorCodigoQR(ventana_segundos=30)
    t = 1_000_000.0
    codigo = g.generar("secreto", 1, instante=t)
    assert g.es_valido("secreto", 1, codigo, instante=t)
    assert g.es_valido("secreto", 1, codigo, instante=t + 30)      # ventana siguiente: aún vale
    assert not g.es_valido("secreto", 1, codigo, instante=t + 60)  # dos ventanas después: expiró
    assert not g.es_valido("otro", 1, codigo, instante=t)           # otro secreto
    assert not g.es_valido("secreto", 2, codigo, instante=t)        # otra clase


def test_lector_csv_normaliza_y_deduplica():
    csv = "Nombres;Apellidos;Cédula\nana maria;pérez;V-12.345.678\nluis;gomez;9876543\nANA;PEREZ;12345678\n;;\nx;;1\n"
    r = LectorMatricula().leer("lista.csv", csv.encode("utf-8"))
    assert sorted(f.cedula for f in r.filas) == ["12345678", "9876543"]
    assert next(f for f in r.filas if f.cedula == "12345678").nombres == "Ana"
    assert r.errores == ["Fila 6: datos incompletos"]


def test_lector_detecta_columnas_faltantes():
    r = LectorMatricula().leer("lista.csv", b"nombre,cedula\nana,1\n")
    assert r.filas == [] and "Faltan columnas" in r.errores[0]
