"""Modelos de datos (tablas) usando el ORM de SQLAlchemy.

Diagrama entidad-relación simplificado:

    Usuario (coordinador | docente)
       │ 1                       │ 1
       │ coordina                │ dicta
       ▼ N                       ▼ N
    Seccion ─────────────────────┘
       │ 1                 N ┌──────────────┐ N            1
       ├────────────────────►│ Inscripcion  │◄──────────── Estudiante
       │                     └──────────────┘
       │ 1
       ▼ N
     Clase  (un día de clase en el que se proyecta un QR)
       │ 1
       ▼ N
    Asistencia ─────────────────────────────────────────► Estudiante

Nota de nombres: llamamos "Clase" a cada encuentro (sesión de clase) para no
confundirlo con la "sesión" de base de datos de SQLAlchemy.
"""
import enum
import secrets
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def ahora() -> datetime:
    return datetime.now(timezone.utc)


class Rol(str, enum.Enum):
    COORDINADOR = "coordinador"
    DOCENTE = "docente"


class Usuario(Base):
    """Persona que inicia sesión en el sistema (los alumnos NO inician sesión)."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    clave_hash: Mapped[str] = mapped_column(String(200))
    rol: Mapped[Rol] = mapped_column(Enum(Rol))

    secciones_dictadas: Mapped[list["Seccion"]] = relationship(
        back_populates="docente", foreign_keys="Seccion.docente_id"
    )


class Estudiante(Base):
    """Alumno identificado por su cédula. Puede estar en varias secciones."""

    __tablename__ = "estudiantes"

    id: Mapped[int] = mapped_column(primary_key=True)
    cedula: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nombres: Mapped[str] = mapped_column(String(100))
    apellidos: Mapped[str] = mapped_column(String(100))

    @property
    def nombre_completo(self) -> str:
        return f"{self.apellidos}, {self.nombres}"


class Seccion(Base):
    """Dominio principal: una sección de una asignatura."""

    __tablename__ = "secciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    asignatura: Mapped[str] = mapped_column(String(120))
    coordinador_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    docente_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)

    coordinador: Mapped[Usuario] = relationship(foreign_keys=[coordinador_id])
    docente: Mapped[Usuario | None] = relationship(
        back_populates="secciones_dictadas", foreign_keys=[docente_id]
    )
    inscripciones: Mapped[list["Inscripcion"]] = relationship(
        back_populates="seccion", cascade="all, delete-orphan"
    )
    clases: Mapped[list["Clase"]] = relationship(
        back_populates="seccion", cascade="all, delete-orphan", order_by="Clase.fecha"
    )

    @property
    def estudiantes(self) -> list[Estudiante]:
        return [i.estudiante for i in self.inscripciones]


class Inscripcion(Base):
    """Tabla puente N:M entre Seccion y Estudiante (la "matrícula")."""

    __tablename__ = "inscripciones"
    __table_args__ = (UniqueConstraint("seccion_id", "estudiante_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    seccion_id: Mapped[int] = mapped_column(ForeignKey("secciones.id", ondelete="CASCADE"))
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiantes.id"))

    seccion: Mapped[Seccion] = relationship(back_populates="inscripciones")
    estudiante: Mapped[Estudiante] = relationship()


class Clase(Base):
    """Un encuentro de clase. Mientras está `abierta`, su QR acepta asistencias."""

    __tablename__ = "clases"

    id: Mapped[int] = mapped_column(primary_key=True)
    seccion_id: Mapped[int] = mapped_column(ForeignKey("secciones.id", ondelete="CASCADE"))
    fecha: Mapped[date] = mapped_column(Date, default=date.today)
    tema: Mapped[str] = mapped_column(String(200), default="")
    abierta: Mapped[bool] = mapped_column(default=True)
    # Secreto propio de la clase con el que se derivan los códigos rotativos del QR.
    secreto: Mapped[str] = mapped_column(String(64), default=lambda: secrets.token_hex(16))
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

    seccion: Mapped[Seccion] = relationship(back_populates="clases")
    asistencias: Mapped[list["Asistencia"]] = relationship(
        back_populates="clase", cascade="all, delete-orphan"
    )


class Asistencia(Base):
    """Registro de que un estudiante estuvo presente en una clase.

    La restricción única (clase, estudiante) garantiza a nivel de base de datos
    que nadie quede marcado dos veces en la misma clase.
    """

    __tablename__ = "asistencias"
    __table_args__ = (UniqueConstraint("clase_id", "estudiante_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    clase_id: Mapped[int] = mapped_column(ForeignKey("clases.id", ondelete="CASCADE"))
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiantes.id"))
    marcada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

    clase: Mapped[Clase] = relationship(back_populates="asistencias")
    estudiante: Mapped[Estudiante] = relationship()
