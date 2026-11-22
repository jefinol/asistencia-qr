"""Punto de entrada de la aplicación (monolito).

Un solo proceso sirve:
  - /api/...     → la API REST (FastAPI)
  - /api/docs    → documentación interactiva automática (Swagger)
  - /...         → el frontend React ya compilado (carpeta static/), en local/Docker

En Vercel el frontend lo sirve la CDN de Vercel y esta app solo atiende /api
(ver api/index.py en la raíz del repo).

Ejecutar en desarrollo:  uv run uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .config import settings
from .database import Base, SessionLocal, engine
from .models import Rol, Usuario
from .routers import auth, clases, secciones
from .security import hashear_clave


def inicializar_base_de_datos():
    """Crea las tablas que falten y el coordinador inicial (ADMIN_USUARIO / ADMIN_CLAVE).

    Es idempotente: se puede llamar en cada arranque. `create_all` no toca las
    tablas que ya existen. Para un MVP académico es suficiente; en un proyecto
    que evoluciona mucho se usarían migraciones con Alembic.
    """
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(Usuario).where(Usuario.rol == Rol.COORDINADOR)) is None:
            db.add(Usuario(usuario=settings.admin_usuario, nombre="Coordinador",
                           clave_hash=hashear_clave(settings.admin_clave), rol=Rol.COORDINADOR))
            try:
                db.commit()
            except IntegrityError:  # dos arranques simultáneos (serverless): ya lo creó el otro
                db.rollback()


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    inicializar_base_de_datos()
    yield


app = FastAPI(title="Asistencia QR", version="0.1.0", lifespan=ciclo_de_vida,
              docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)
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
