"""Inicio de sesión y gestión de docentes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Rol, Usuario
from ..schemas import DocenteIn, LoginIn, LoginOut, UsuarioOut
from ..security import crear_token, hashear_clave, solo_coordinador, usuario_actual, verificar_clave

router = APIRouter(prefix="/api", tags=["usuarios"])


@router.post("/auth/login", response_model=LoginOut)
def login(datos: LoginIn, db: Session = Depends(get_db)):
    usuario = db.scalar(select(Usuario).where(Usuario.usuario == datos.usuario.strip().lower()))
    if usuario is None or not verificar_clave(datos.clave, usuario.clave_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario o clave incorrectos")
    return LoginOut(token=crear_token(usuario), usuario=usuario)


@router.get("/auth/yo", response_model=UsuarioOut)
def yo(usuario: Usuario = Depends(usuario_actual)):
    return usuario


@router.get("/docentes", response_model=list[UsuarioOut])
def listar_docentes(db: Session = Depends(get_db), _: Usuario = Depends(solo_coordinador)):
    return db.scalars(select(Usuario).where(Usuario.rol == Rol.DOCENTE).order_by(Usuario.nombre)).all()


@router.post("/docentes", response_model=UsuarioOut, status_code=201)
def crear_docente(datos: DocenteIn, db: Session = Depends(get_db), _: Usuario = Depends(solo_coordinador)):
    nombre_usuario = datos.usuario.strip().lower()
    if db.scalar(select(Usuario).where(Usuario.usuario == nombre_usuario)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ese nombre de usuario ya existe")
    docente = Usuario(
        usuario=nombre_usuario, nombre=datos.nombre.strip(),
        clave_hash=hashear_clave(datos.clave), rol=Rol.DOCENTE,
    )
    db.add(docente)
    db.commit()
    return docente
