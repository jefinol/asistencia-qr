"""Clases (encuentros), QR rotativo y marcaje de asistencia.

Rutas privadas (docente/coordinador) bajo /api/clases y rutas PÚBLICAS para el
alumno bajo /api/publico (el alumno no tiene cuenta: solo escanea y pone su cédula).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Asistencia, Clase, Estudiante, Inscripcion, Usuario
from ..schemas import (AsistenteOut, ClaseIn, ClaseOut, InfoClasePublica, MarcarIn, MarcarOut, QRActual)
from ..security import usuario_actual
from ..services.codigo_qr import GeneradorCodigoQR
from ..services.matricula import LectorMatricula
from .secciones import obtener_seccion

router = APIRouter(prefix="/api", tags=["clases"])
generador_qr = GeneradorCodigoQR(ventana_segundos=settings.qr_ventana_segundos)


def obtener_clase(db: Session, clase_id: int, usuario: Usuario) -> Clase:
    clase = db.get(Clase, clase_id)
    if clase is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Clase no encontrada")
    obtener_seccion(db, clase.seccion_id, usuario)  # valida permisos sobre la sección
    return clase


# ---------- Privadas ----------
@router.get("/secciones/{seccion_id}/clases", response_model=list[ClaseOut])
def listar_clases(seccion_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    return list(reversed(obtener_seccion(db, seccion_id, usuario).clases))


@router.post("/secciones/{seccion_id}/clases", response_model=ClaseOut, status_code=201)
def abrir_clase(seccion_id: int, datos: ClaseIn, db: Session = Depends(get_db),
                usuario: Usuario = Depends(usuario_actual)):
    """Crea la clase de hoy y la deja abierta para recibir asistencias."""
    seccion = obtener_seccion(db, seccion_id, usuario)
    clase = Clase(seccion_id=seccion.id, tema=datos.tema.strip())
    db.add(clase)
    db.commit()
    return clase


@router.get("/clases/{clase_id}", response_model=ClaseOut)
def ver_clase(clase_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    return obtener_clase(db, clase_id, usuario)


@router.get("/clases/{clase_id}/qr", response_model=QRActual)
def qr_actual(clase_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    """El frontend del docente llama esto periódicamente para refrescar el QR proyectado."""
    clase = obtener_clase(db, clase_id, usuario)
    return QRActual(
        codigo=generador_qr.generar(clase.secreto, clase.id),
        segundos_restantes=generador_qr.segundos_restantes(),
        presentes=len(clase.asistencias),
        inscritos=len(clase.seccion.inscripciones),
        abierta=clase.abierta,
    )


@router.post("/clases/{clase_id}/cerrar", response_model=ClaseOut)
def cerrar_clase(clase_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    clase = obtener_clase(db, clase_id, usuario)
    clase.abierta = False
    db.commit()
    return clase


@router.post("/clases/{clase_id}/reabrir", response_model=ClaseOut)
def reabrir_clase(clase_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    clase = obtener_clase(db, clase_id, usuario)
    clase.abierta = True
    db.commit()
    return clase


@router.delete("/clases/{clase_id}", status_code=204)
def eliminar_clase(clase_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    db.delete(obtener_clase(db, clase_id, usuario))
    db.commit()


@router.get("/clases/{clase_id}/asistentes", response_model=list[AsistenteOut])
def asistentes(clase_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    """Lista de toda la sección indicando quién está presente (para pasar lista manual)."""
    clase = obtener_clase(db, clase_id, usuario)
    presentes = {a.estudiante_id for a in clase.asistencias}  # set → búsqueda O(1)
    filas = [
        AsistenteOut(estudiante_id=e.id, cedula=e.cedula, nombre=e.nombre_completo, presente=e.id in presentes)
        for e in clase.seccion.estudiantes
    ]
    return sorted(filas, key=lambda f: f.nombre)


@router.put("/clases/{clase_id}/asistentes/{estudiante_id}", response_model=AsistenteOut)
def alternar_asistencia(clase_id: int, estudiante_id: int, db: Session = Depends(get_db),
                        usuario: Usuario = Depends(usuario_actual)):
    """Marca/desmarca manualmente (alumno sin teléfono, error, etc.)."""
    clase = obtener_clase(db, clase_id, usuario)
    estudiante = next((e for e in clase.seccion.estudiantes if e.id == estudiante_id), None)
    if estudiante is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El estudiante no está en la sección")
    existente = next((a for a in clase.asistencias if a.estudiante_id == estudiante_id), None)
    if existente:
        db.delete(existente)
    else:
        db.add(Asistencia(clase_id=clase.id, estudiante_id=estudiante_id))
    db.commit()
    return AsistenteOut(estudiante_id=estudiante.id, cedula=estudiante.cedula,
                        nombre=estudiante.nombre_completo, presente=existente is None)


# ---------- Públicas (alumno) ----------
@router.get("/publico/clases/{clase_id}", response_model=InfoClasePublica)
def info_publica(clase_id: int, c: str = "", db: Session = Depends(get_db)):
    """Lo que ve el alumno al abrir el enlace del QR, antes de poner su cédula."""
    clase = db.get(Clase, clase_id)
    if clase is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Clase no encontrada")
    return InfoClasePublica(
        seccion=clase.seccion.codigo, asignatura=clase.seccion.asignatura, fecha=clase.fecha,
        tema=clase.tema, codigo_valido=clase.abierta and generador_qr.es_valido(clase.secreto, clase.id, c),
    )


@router.post("/publico/asistencia", response_model=MarcarOut)
def marcar(datos: MarcarIn, db: Session = Depends(get_db)):
    """Algoritmo de validación del marcaje (en orden, se detiene en el primer fallo):

    1. La clase existe y está abierta.
    2. El código del QR es el vigente (o el inmediatamente anterior).
    3. La cédula pertenece a un estudiante inscrito en la sección.
    4. No había marcado antes (lo garantiza también la restricción UNIQUE).
    """
    clase = db.get(Clase, datos.clase_id)
    if clase is None or not clase.abierta:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La clase no está recibiendo asistencias")
    if not generador_qr.es_valido(clase.secreto, clase.id, datos.codigo):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El código QR expiró. Escanéalo de nuevo.")

    cedula = LectorMatricula.normalizar_cedula(datos.cedula)
    estudiante = db.scalar(
        select(Estudiante).join(Inscripcion)
        .where(Estudiante.cedula == cedula, Inscripcion.seccion_id == clase.seccion_id)
    )
    if estudiante is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tu cédula no está inscrita en esta sección")

    db.add(Asistencia(clase_id=clase.id, estudiante_id=estudiante.id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return MarcarOut(mensaje="Ya tenías la asistencia registrada", estudiante=estudiante.nombre_completo)
    return MarcarOut(mensaje="¡Asistencia registrada!", estudiante=estudiante.nombre_completo)
