"""Cálculo de estadísticas de asistencia.

Algoritmo (por sección), con E = estudiantes inscritos, C = clases dictadas,
A = asistencias registradas:

1. Una sola consulta trae todos los pares (clase_id, estudiante_id) de la sección.
2. Se recorren una vez construyendo dos contadores (`collections.Counter`, que
   es un diccionario/tabla hash):
       por_estudiante[estudiante_id] += 1
       por_clase[clase_id]           += 1
3. Porcentaje de un estudiante  = asistencias / C * 100
   Porcentaje de una clase      = presentes   / E * 100
   Promedio de la sección       = A / (E * C) * 100

Complejidad: O(A + E + C) tiempo y O(E + C) memoria, es decir lineal: se evita
hacer una consulta por estudiante (el clásico problema "N+1").

Un estudiante está "en riesgo" si su asistencia es menor a UMBRAL_RIESGO (75 %),
que es el mínimo típico exigido en reglamentos universitarios.
"""
from collections import Counter
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Asistencia, Clase, Seccion

UMBRAL_RIESGO = 75.0


def _pct(parte: int, total: int) -> float:
    return round(parte * 100 / total, 1) if total else 0.0


@dataclass
class EstadisticaEstudiante:
    estudiante_id: int
    cedula: str
    nombres: str
    apellidos: str
    asistencias: int
    inasistencias: int
    porcentaje: float
    en_riesgo: bool


@dataclass
class EstadisticaClase:
    clase_id: int
    fecha: date
    tema: str
    abierta: bool
    presentes: int
    porcentaje: float


@dataclass
class ResumenSeccion:
    seccion_id: int
    codigo: str
    asignatura: str
    docente: str | None
    total_estudiantes: int
    total_clases: int
    promedio_asistencia: float
    estudiantes_en_riesgo: int


@dataclass
class ReporteSeccion:
    resumen: ResumenSeccion
    estudiantes: list[EstadisticaEstudiante] = field(default_factory=list)
    clases: list[EstadisticaClase] = field(default_factory=list)


@dataclass
class ResumenGeneral:
    total_secciones: int
    total_estudiantes: int
    total_clases: int
    promedio_asistencia: float
    secciones: list[ResumenSeccion] = field(default_factory=list)


class CalculadoraEstadisticas:
    def __init__(self, db: Session):
        self.db = db

    def reporte_seccion(self, seccion: Seccion) -> ReporteSeccion:
        estudiantes = seccion.estudiantes
        clases = seccion.clases
        E, C = len(estudiantes), len(clases)

        pares = self.db.execute(
            select(Asistencia.clase_id, Asistencia.estudiante_id)
            .join(Clase)
            .where(Clase.seccion_id == seccion.id)
        ).all()
        inscritos = {e.id for e in estudiantes}  # set: pertenencia en O(1)
        por_estudiante: Counter[int] = Counter()
        por_clase: Counter[int] = Counter()
        for clase_id, estudiante_id in pares:
            if estudiante_id in inscritos:  # ignora a quien ya fue retirado de la sección
                por_estudiante[estudiante_id] += 1
                por_clase[clase_id] += 1

        filas_est = [
            EstadisticaEstudiante(
                estudiante_id=e.id,
                cedula=e.cedula,
                nombres=e.nombres,
                apellidos=e.apellidos,
                asistencias=por_estudiante[e.id],
                inasistencias=C - por_estudiante[e.id],
                porcentaje=(p := _pct(por_estudiante[e.id], C)),
                en_riesgo=C > 0 and p < UMBRAL_RIESGO,
            )
            for e in estudiantes
        ]
        filas_est.sort(key=lambda f: (f.apellidos, f.nombres))

        filas_clase = [
            EstadisticaClase(c.id, c.fecha, c.tema, c.abierta, por_clase[c.id], _pct(por_clase[c.id], E))
            for c in clases
        ]

        resumen = ResumenSeccion(
            seccion_id=seccion.id,
            codigo=seccion.codigo,
            asignatura=seccion.asignatura,
            docente=seccion.docente.nombre if seccion.docente else None,
            total_estudiantes=E,
            total_clases=C,
            promedio_asistencia=_pct(sum(por_clase.values()), E * C),
            estudiantes_en_riesgo=sum(f.en_riesgo for f in filas_est),
        )
        return ReporteSeccion(resumen, filas_est, filas_clase)

    def resumen_general(self, secciones: list[Seccion]) -> ResumenGeneral:
        """Dashboard del coordinador: agrega los resúmenes de todas sus secciones.

        El promedio general es PONDERADO (suma de asistencias / suma de cupos
        posibles), no el promedio simple de los porcentajes, para que una sección
        de 5 alumnos no pese igual que una de 40.
        """
        resumenes = [self.reporte_seccion(s).resumen for s in secciones]
        posibles = sum(r.total_estudiantes * r.total_clases for r in resumenes)
        logradas = sum(r.promedio_asistencia / 100 * r.total_estudiantes * r.total_clases for r in resumenes)
        return ResumenGeneral(
            total_secciones=len(resumenes),
            total_estudiantes=sum(r.total_estudiantes for r in resumenes),
            total_clases=sum(r.total_clases for r in resumenes),
            promedio_asistencia=round(logradas * 100 / posibles, 1) if posibles else 0.0,
            secciones=resumenes,
        )
