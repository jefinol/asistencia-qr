"""Conexión a la base de datos (SQLAlchemy 2.0).

Usamos SQLite: es un solo archivo, no necesita servidor y sobra para una
universidad/curso. Si algún día se quiere PostgreSQL basta con cambiar
DATABASE_URL; el resto del código no cambia gracias al ORM.
"""
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

if settings.database_url.startswith("sqlite:///"):
    # Asegura que exista la carpeta donde vive el archivo .db
    Path(settings.database_url.removeprefix("sqlite:///")).parent.mkdir(
        parents=True, exist_ok=True
    )

engine = create_engine(
    settings.database_url,
    # SQLite + FastAPI: las peticiones pueden atenderse en hilos distintos.
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)


@event.listens_for(engine, "connect")
def _activar_foreign_keys(dbapi_conn, _):
    """SQLite no valida claves foráneas a menos que se lo pidamos."""
    if "sqlite" in settings.database_url:
        dbapi_conn.execute("PRAGMA foreign_keys=ON")


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Clase base de todos los modelos ORM."""


def get_db():
    """Dependencia de FastAPI: abre una sesión por petición y la cierra al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
