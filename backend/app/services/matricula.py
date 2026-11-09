"""Lectura del archivo de matrícula (CSV o Excel) que sube el coordinador.

Formato esperado (la primera fila es el encabezado, en cualquier orden):

    nombres | apellidos | cedula

Estructuras de datos usadas:
- `dict[str, FilaMatricula]` indexado por cédula: elimina duplicados dentro del
  mismo archivo en O(1) por fila (la última aparición gana).
- Lista de errores con el número de fila para que el coordinador sepa qué corregir.
"""
import csv
import io
import re
from dataclasses import dataclass, field

from openpyxl import load_workbook

COLUMNAS = ("nombres", "apellidos", "cedula")


@dataclass
class FilaMatricula:
    cedula: str
    nombres: str
    apellidos: str


@dataclass
class ResultadoLectura:
    filas: list[FilaMatricula] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)


class LectorMatricula:
    """Convierte un archivo subido en una lista limpia de estudiantes."""

    @staticmethod
    def normalizar_cedula(valor) -> str:
        """'V-12.345.678' → '12345678'. Deja solo dígitos."""
        if isinstance(valor, float):  # Excel a veces guarda 12345678 como 12345678.0
            valor = int(valor)
        return re.sub(r"\D", "", str(valor or ""))

    @staticmethod
    def _normalizar_encabezado(texto) -> str:
        t = str(texto or "").strip().lower()
        return t.replace("é", "e").replace("í", "i").replace("ó", "o")

    def _filas_crudas(self, nombre_archivo: str, contenido: bytes) -> list[list]:
        if nombre_archivo.lower().endswith((".xlsx", ".xlsm")):
            libro = load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
            return [list(f) for f in libro.active.iter_rows(values_only=True)]
        # CSV: probamos UTF-8 (con o sin BOM) y si falla Latin-1 (Excel en Windows).
        try:
            texto = contenido.decode("utf-8-sig")
        except UnicodeDecodeError:
            texto = contenido.decode("latin-1")
        dialecto = csv.Sniffer().sniff(texto.splitlines()[0], delimiters=",;\t")
        return list(csv.reader(io.StringIO(texto), dialecto))

    def leer(self, nombre_archivo: str, contenido: bytes) -> ResultadoLectura:
        resultado = ResultadoLectura()
        try:
            filas = self._filas_crudas(nombre_archivo, contenido)
        except Exception:
            resultado.errores.append("No se pudo leer el archivo. Use CSV o XLSX.")
            return resultado
        if not filas:
            resultado.errores.append("El archivo está vacío.")
            return resultado

        encabezado = [self._normalizar_encabezado(c) for c in filas[0]]
        faltantes = [c for c in COLUMNAS if c not in encabezado]
        if faltantes:
            resultado.errores.append(f"Faltan columnas: {', '.join(faltantes)}")
            return resultado
        idx = {c: encabezado.index(c) for c in COLUMNAS}

        por_cedula: dict[str, FilaMatricula] = {}
        for numero, fila in enumerate(filas[1:], start=2):
            if not any(fila):
                continue  # fila vacía
            celda = lambda c: fila[idx[c]] if idx[c] < len(fila) else ""
            cedula = self.normalizar_cedula(celda("cedula"))
            nombres = str(celda("nombres") or "").strip()
            apellidos = str(celda("apellidos") or "").strip()
            if not cedula or not nombres or not apellidos:
                resultado.errores.append(f"Fila {numero}: datos incompletos")
                continue
            por_cedula[cedula] = FilaMatricula(cedula, nombres.title(), apellidos.title())

        resultado.filas = list(por_cedula.values())
        return resultado
