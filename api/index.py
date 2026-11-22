"""Entrada de la API en Vercel (función serverless de Python).

Vercel ejecuta este archivo para todas las rutas /api/* (ver vercel.json).
No duplica código: solo importa la misma app FastAPI que corre en local y en
Docker, que vive en backend/app/.

El frontend NO pasa por aquí: Vercel compila frontend/ con Vite y sirve los
archivos estáticos desde su CDN.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app, inicializar_base_de_datos  # noqa: E402

# En serverless no siempre se ejecuta el "lifespan" de FastAPI, así que
# preparamos la base de datos al cargar la función (es idempotente).
inicializar_base_de_datos()

__all__ = ["app"]
