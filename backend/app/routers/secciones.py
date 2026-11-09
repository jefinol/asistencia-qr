"""Secciones: CRUD (coordinador), matrícula, estadísticas y reportes."""
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Estudiante, Inscripcion, Rol, Seccion, Usuario
from ..schemas import EstudianteOut, ResultadoMatricula, SeccionIn, SeccionOut
from ..security import solo_coordinador, usuario_actual
from ..services.estadisticas import CalculadoraEstadisticas, ReporteSeccion, ResumenGeneral
from ..services.matricula import LectorMatricula
from ..services.reportes import GENERADORES

router = APIRouter(prefix="/api", tags=["secciones"])


# ---------- Reglas de acceso ----------
def puede_ver(usuario: Usuario, seccion: Seccion) -> bool:
    """El coordinador ve sus secciones; el docente solo las que dicta."""
    if usuario.rol == Rol.COORDINADOR:
        return seccion.coordinador_id == usuario.id
    return seccion.docente_id == usuario.id


def obtener_seccion(db: Session, seccion_id: int, usuario: Usuario) -> Seccion:
    seccion = db.get(Seccion, seccion_id)
    if seccion is None or not puede_ver(usuario, seccion):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sección no encontrada")
    return seccion


def _validar_docente(db: Session, docente_id: int | None):
    if docente_id is not None:
        docente = db.get(Usuario, docente_id)
        if docente is None or docente.rol != Rol.DOCENTE:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Docente inválido")


# ---------- CRUD ----------
@router.get("/secciones", response_model=list[SeccionOut])
def listar(db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    campo = Seccion.coordinador_id if usuario.rol == Rol.COORDINADOR else Seccion.docente_id
    return db.scalars(select(Seccion).where(campo == usuario.id).order_by(Seccion.codigo)).all()


@router.post("/secciones", response_model=SeccionOut, status_code=201)
def crear(datos: SeccionIn, db: Session = Depends(get_db), coord: Usuario = Depends(solo_coordinador)):
    codigo = datos.codigo.strip().upper()
    if db.scalar(select(Seccion).where(Seccion.codigo == codigo)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una sección con ese código")
    _validar_docente(db, datos.docente_id)
    seccion = Seccion(codigo=codigo, asignatura=datos.asignatura.strip(),
                      docente_id=datos.docente_id, coordinador_id=coord.id)
    db.add(seccion)
    db.commit()
    return seccion


@router.put("/secciones/{seccion_id}", response_model=SeccionOut)
def editar(seccion_id: int, datos: SeccionIn, db: Session = Depends(get_db),
           coord: Usuario = Depends(solo_coordinador)):
    seccion = obtener_seccion(db, seccion_id, coord)
    codigo = datos.codigo.strip().upper()
    otra = db.scalar(select(Seccion).where(Seccion.codigo == codigo))
    if otra and otra.id != seccion.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una sección con ese código")
    _validar_docente(db, datos.docente_id)
    seccion.codigo, seccion.asignatura, seccion.docente_id = codigo, datos.asignatura.strip(), datos.docente_id
    db.commit()
    return seccion


@router.delete("/secciones/{seccion_id}", status_code=204)
def eliminar(seccion_id: int, db: Session = Depends(get_db), coord: Usuario = Depends(solo_coordinador)):
    db.delete(obtener_seccion(db, seccion_id, coord))
    db.commit()


# ---------- Matrícula ----------
@router.get("/secciones/{seccion_id}/estudiantes", response_model=list[EstudianteOut])
def estudiantes(seccion_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    seccion = obtener_seccion(db, seccion_id, usuario)
    return sorted(seccion.estudiantes, key=lambda e: (e.apellidos, e.nombres))


@router.post("/secciones/{seccion_id}/matricula", response_model=ResultadoMatricula)
async def cargar_matricula(seccion_id: int, archivo: UploadFile = File(...),
                           db: Session = Depends(get_db), coord: Usuario = Depends(solo_coordinador)):
    """Sube un CSV/XLSX con columnas nombres, apellidos, cedula.

    - Si la cédula no existe, se crea el estudiante.
    - Si ya existe (p. ej. está en otra sección), se reutiliza y se actualizan sus nombres.
    - Si ya estaba inscrito en esta sección, se cuenta como "ya inscrito".
    """
    seccion = obtener_seccion(db, seccion_id, coord)
    lectura = LectorMatricula().leer(archivo.filename or "", await archivo.read())

    cedulas = [f.cedula for f in lectura.filas]
    # dict cédula → Estudiante: una sola consulta en vez de una por fila.
    existentes = {e.cedula: e for e in db.scalars(select(Estudiante).where(Estudiante.cedula.in_(cedulas)))}
    ya_en_seccion = {e.cedula for e in seccion.estudiantes}

    agregados = ya_inscritos = 0
    for fila in lectura.filas:
        estudiante = existentes.get(fila.cedula)
        if estudiante is None:
            estudiante = Estudiante(cedula=fila.cedula, nombres=fila.nombres, apellidos=fila.apellidos)
            db.add(estudiante)
        else:
            estudiante.nombres, estudiante.apellidos = fila.nombres, fila.apellidos
        if fila.cedula in ya_en_seccion:
            ya_inscritos += 1
        else:
            seccion.inscripciones.append(Inscripcion(estudiante=estudiante))
            agregados += 1
    db.commit()
    return ResultadoMatricula(agregados=agregados, ya_inscritos=ya_inscritos, errores=lectura.errores)


@router.delete("/secciones/{seccion_id}/estudiantes/{estudiante_id}", status_code=204)
def retirar(seccion_id: int, estudiante_id: int, db: Session = Depends(get_db),
            coord: Usuario = Depends(solo_coordinador)):
    seccion = obtener_seccion(db, seccion_id, coord)
    inscripcion = next((i for i in seccion.inscripciones if i.estudiante_id == estudiante_id), None)
    if inscripcion is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El estudiante no está en la sección")
    db.delete(inscripcion)
    db.commit()


# ---------- Estadísticas y reportes ----------
@router.get("/estadisticas/general", response_model=ResumenGeneral)
def resumen_general(db: Session = Depends(get_db), coord: Usuario = Depends(solo_coordinador)):
    secciones = db.scalars(select(Seccion).where(Seccion.coordinador_id == coord.id).order_by(Seccion.codigo)).all()
    return CalculadoraEstadisticas(db).resumen_general(list(secciones))


@router.get("/secciones/{seccion_id}/estadisticas", response_model=ReporteSeccion)
def estadisticas(seccion_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    return CalculadoraEstadisticas(db).reporte_seccion(obtener_seccion(db, seccion_id, usuario))


@router.get("/secciones/{seccion_id}/reporte")
def reporte(seccion_id: int, formato: str = Query("pdf", pattern="^(pdf|excel)$"),
            db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    datos = CalculadoraEstadisticas(db).reporte_seccion(obtener_seccion(db, seccion_id, usuario))
    generador = GENERADORES[formato]
    return Response(
        content=generador.generar(datos),
        media_type=generador.tipo_mime,
        headers={"Content-Disposition": f'attachment; filename="{generador.nombre_archivo(datos)}"'},
    )
