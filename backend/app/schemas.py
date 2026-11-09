"""Esquemas Pydantic: definen y validan el JSON que entra y sale de la API.

Se separan de los modelos ORM a propósito: así nunca devolvemos por accidente
campos internos como `clave_hash` o el `secreto` de una clase.
"""
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from .models import Rol


class _ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Usuarios ----------
class LoginIn(BaseModel):
    usuario: str
    clave: str


class UsuarioOut(_ORM):
    id: int
    usuario: str
    nombre: str
    rol: Rol


class LoginOut(BaseModel):
    token: str
    usuario: UsuarioOut


class DocenteIn(BaseModel):
    usuario: str = Field(min_length=3, max_length=50)
    nombre: str = Field(min_length=3, max_length=120)
    clave: str = Field(min_length=6)


# ---------- Secciones ----------
class SeccionIn(BaseModel):
    codigo: str = Field(min_length=1, max_length=20, pattern=r"^[A-Za-z0-9\-]+$")
    asignatura: str = Field(min_length=2, max_length=120)
    docente_id: int | None = None


class SeccionOut(_ORM):
    id: int
    codigo: str
    asignatura: str
    docente: UsuarioOut | None


class EstudianteOut(_ORM):
    id: int
    cedula: str
    nombres: str
    apellidos: str


class ResultadoMatricula(BaseModel):
    agregados: int
    ya_inscritos: int
    errores: list[str]


# ---------- Clases y QR ----------
class ClaseIn(BaseModel):
    tema: str = Field(default="", max_length=200)


class ClaseOut(_ORM):
    id: int
    seccion_id: int
    fecha: date
    tema: str
    abierta: bool


class QRActual(BaseModel):
    codigo: str
    segundos_restantes: int
    presentes: int
    inscritos: int
    abierta: bool


class AsistenteOut(BaseModel):
    estudiante_id: int
    cedula: str
    nombre: str
    presente: bool


# ---------- Público (alumno) ----------
class InfoClasePublica(BaseModel):
    seccion: str
    asignatura: str
    fecha: date
    tema: str
    codigo_valido: bool


class MarcarIn(BaseModel):
    clase_id: int
    codigo: str
    cedula: str = Field(min_length=1, max_length=20)


class MarcarOut(BaseModel):
    mensaje: str
    estudiante: str
