"""Punto de entrada de la aplicación (monolito).

Un solo proceso sirve:
  - /api/...   → la API REST (FastAPI)
  - /docs      → documentación interactiva automática (Swagger)
  - /...       → el frontend React ya compilado (carpeta static/)

Ejecutar en desarrollo:  uv run uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from .config import settings
from .database import Base, SessionLocal, engine
from .models import Rol, Usuario
from .routers import auth, clases, secciones
from .security import hashear_clave


def crear_coordinador_inicial():
    """Si no hay ningún coordinador, crea uno con ADMIN_USUARIO / ADMIN_CLAVE."""
    with SessionLocal() as db:
        if db.scalar(select(Usuario).where(Usuario.rol == Rol.COORDINADOR)) is None:
            db.add(Usuario(usuario=settings.admin_usuario, nombre="Coordinador",
                           clave_hash=hashear_clave(settings.admin_clave), rol=Rol.COORDINADOR))
            db.commit()


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    # create_all crea las tablas que falten. Para un MVP académico es suficiente;
    # en un proyecto que evoluciona mucho se usaría Alembic para migraciones.
    Base.metadata.create_all(engine)
    crear_coordinador_inicial()
    yield


app = FastAPI(title="Asistencia QR", version="0.1.0", lifespan=ciclo_de_vida)
app.include_router(auth.router)
app.include_router(secciones.router)
app.include_router(clases.router)


@app.get("/api/salud", tags=["sistema"])
def salud():
    return {"ok": True}


# ---------- Frontend (SPA) ----------
# Solo si existe el build (en desarrollo el frontend corre aparte con Vite).
if (settings.static_dir / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=settings.static_dir / "assets"), name="assets")

    @app.get("/{ruta:path}", include_in_schema=False)
    def spa(ruta: str):
        """Cualquier ruta que no sea de la API devuelve index.html y React Router decide qué mostrar."""
        if ruta.startswith("api/"):
            raise HTTPException(404, "Ruta de API inexistente")
        raiz = settings.static_dir.resolve()
        archivo = (raiz / ruta).resolve()
        if ruta and archivo.is_file() and raiz in archivo.parents:  # evita salir de static/
            return FileResponse(archivo)
        return FileResponse(settings.static_dir / "index.html")
