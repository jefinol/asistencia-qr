"""Inicio de sesión, cambio de clave y gestión de docentes.

Alcance del MVP: existe UN coordinador, creado automáticamente al arrancar
(ADMIN_USUARIO / ADMIN_CLAVE). El coordinador gestiona docentes, pero NO crea
otros coordinadores: en un escenario real eso le correspondería a un
superusuario (p. ej. Control de Estudios), que queda fuera del alcance.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Rol, Seccion, Usuario
from ..schemas import CambioClave, DocenteEditar, DocenteIn, LoginIn, LoginOut, UsuarioOut
from ..security import crear_token, hashear_clave, solo_coordinador, usuario_actual, verificar_clave

router = APIRouter(prefix="/api", tags=["usuarios"])


# ---------- Sesión ----------
@router.post("/auth/login", response_model=LoginOut)
def login(datos: LoginIn, db: Session = Depends(get_db)):
    usuario = db.scalar(select(Usuario).where(Usuario.usuario == datos.usuario.strip().lower()))
    if usuario is None or not verificar_clave(datos.clave, usuario.clave_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario o clave incorrectos")
    return LoginOut(token=crear_token(usuario), usuario=usuario)


@router.get("/auth/yo", response_model=UsuarioOut)
def yo(usuario: Usuario = Depends(usuario_actual)):
    return usuario


@router.put("/auth/clave", status_code=204)
def cambiar_mi_clave(datos: CambioClave, db: Session = Depends(get_db),
                     usuario: Usuario = Depends(usuario_actual)):
    """Cualquier usuario (docente o coordinador) cambia su propia clave, confirmando la actual."""
    if not verificar_clave(datos.clave_actual, usuario.clave_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La clave actual no es correcta")
    usuario.clave_hash = hashear_clave(datos.clave_nueva)
    db.commit()


# ---------- Gestión de docentes (solo coordinador) ----------
def _obtener_docente(db: Session, docente_id: int) -> Usuario:
    docente = db.get(Usuario, docente_id)
    if docente is None or docente.rol != Rol.DOCENTE:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Docente no encontrado")
    return docente


@router.get("/docentes", response_model=list[UsuarioOut])
def listar_docentes(db: Session = Depends(get_db), _: Usuario = Depends(solo_coordinador)):
    return db.scalars(select(Usuario).where(Usuario.rol == Rol.DOCENTE).order_by(Usuario.nombre)).all()


@router.post("/docentes", response_model=UsuarioOut, status_code=201)
def crear_docente(datos: DocenteIn, db: Session = Depends(get_db), _: Usuario = Depends(solo_coordinador)):
    nombre_usuario = datos.usuario.strip().lower()
    if db.scalar(select(Usuario).where(Usuario.usuario == nombre_usuario)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ese nombre de usuario ya existe")
    docente = Usuario(usuario=nombre_usuario, nombre=datos.nombre.strip(),
                      clave_hash=hashear_clave(datos.clave), rol=Rol.DOCENTE)
    db.add(docente)
    db.commit()
    return docente


@router.put("/docentes/{docente_id}", response_model=UsuarioOut)
def editar_docente(docente_id: int, datos: DocenteEditar, db: Session = Depends(get_db),
                   _: Usuario = Depends(solo_coordinador)):
    """Cambia el nombre y, si se envía, reinicia la clave (p. ej. el docente la olvidó)."""
    docente = _obtener_docente(db, docente_id)
    docente.nombre = datos.nombre.strip()
    if datos.clave:
        docente.clave_hash = hashear_clave(datos.clave)
    db.commit()
    return docente


@router.delete("/docentes/{docente_id}", status_code=204)
def eliminar_docente(docente_id: int, db: Session = Depends(get_db), _: Usuario = Depends(solo_coordinador)):
    """Elimina un docente. Sus secciones quedan "sin asignar": no se pierde ninguna asistencia."""
    docente = _obtener_docente(db, docente_id)
    db.execute(update(Seccion).where(Seccion.docente_id == docente.id).values(docente_id=None))
    db.delete(docente)
    db.commit()
