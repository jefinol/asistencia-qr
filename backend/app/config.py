"""Configuración leída de variables de entorno.

Todo lo configurable vive aquí para no tener "números mágicos" regados por el
código. En producción (VPS) se definen en el archivo `.env` que lee docker compose.
"""
import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # carpeta backend/


@dataclass(frozen=True)
class Settings:
    # Clave para firmar los JWT y los códigos QR. ¡Cambiarla en producción!
    secret_key: str = os.getenv("SECRET_KEY", "cambiar-esta-clave-en-produccion")
    # URL de SQLAlchemy. Por defecto un archivo SQLite dentro de backend/data/.
    database_url: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'asistencia.db'}"
    )
    # Duración del token de sesión de docentes/coordinadores.
    token_horas: int = int(os.getenv("TOKEN_HORAS", "12"))
    # Cada cuántos segundos cambia el código del QR proyectado.
    qr_ventana_segundos: int = int(os.getenv("QR_VENTANA_SEGUNDOS", "30"))
    # Carpeta con el build de React (la llena el Dockerfile).
    static_dir: Path = Path(os.getenv("STATIC_DIR", str(BASE_DIR / "static")))
    # Coordinador inicial que se crea si la base de datos está vacía.
    admin_usuario: str = os.getenv("ADMIN_USUARIO", "coordinador")
    admin_clave: str = os.getenv("ADMIN_CLAVE", "coordinador123")


settings = Settings()
