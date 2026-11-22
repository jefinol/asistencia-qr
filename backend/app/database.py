"""Conexión a la base de datos (SQLAlchemy 2.0).

Dos motores posibles, elegidos solo con la variable DATABASE_URL:

- SQLite (por defecto): un archivo local. Ideal para desarrollo y Docker.
- PostgreSQL (Supabase en producción, desplegado en Vercel).

El resto del código no cambia gracias al ORM.

Notas para Supabase + Vercel (serverless):
- Usar la cadena del *pooler* en modo transacción (puerto 6543), que Supabase
  recomienda para funciones serverless que abren muchas conexiones cortas.
- Ese modo NO soporta "prepared statements", por eso se desactivan
  (`prepare_threshold=None` en psycopg).
- `NullPool`: cada petición abre y cierra su conexión; el pooler de Supabase
  es quien las reutiliza. Mantener un pool propio en una función serverless
  dejaría conexiones colgadas entre invocaciones.
"""
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from .config import settings


def _normalizar_url(url: str) -> str:
    """Supabase entrega 'postgresql://...'; SQLAlchemy necesita saber el driver (psycopg 3)."""
    for prefijo in ("postgres://", "postgresql://"):
        if url.startswith(prefijo):
            return "postgresql+psycopg://" + url.removeprefix(prefijo)
    return url


DATABASE_URL = _normalizar_url(settings.database_url)
ES_SQLITE = DATABASE_URL.startswith("sqlite")

if ES_SQLITE:
    # Asegura que exista la carpeta donde vive el archivo .db
    Path(DATABASE_URL.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        DATABASE_URL,
        # SQLite + FastAPI: las peticiones pueden atenderse en hilos distintos.
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _activar_foreign_keys(dbapi_conn, _):
        """SQLite no valida claves foráneas a menos que se lo pidamos."""
        dbapi_conn.execute("PRAGMA foreign_keys=ON")
else:
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        connect_args={
            "prepare_threshold": None,  # requerido por el pooler de Supabase (modo transacción)
            "connect_timeout": 10,      # si la base no responde (p. ej. proyecto pausado), fallar rápido
        },
    )

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
