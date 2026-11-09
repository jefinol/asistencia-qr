"""Autenticación: hash de contraseñas, JWT y control de roles.

- Contraseñas: PBKDF2-HMAC-SHA256 de la librería estándar (hashlib). No hace
  falta instalar bcrypt para un proyecto de este tamaño y es un algoritmo
  recomendado por OWASP.
- Sesión: JWT firmado (HS256) que el frontend guarda y envía en la cabecera
  `Authorization: Bearer <token>`.
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import Rol, Usuario

_ITERACIONES = 200_000


# ---------- Contraseñas ----------
def hashear_clave(clave: str) -> str:
    """Devuelve 'sal$hash' en hexadecimal."""
    sal = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", clave.encode(), sal, _ITERACIONES)
    return f"{sal.hex()}${digest.hex()}"


def verificar_clave(clave: str, guardado: str) -> bool:
    sal_hex, hash_hex = guardado.split("$")
    digest = hashlib.pbkdf2_hmac("sha256", clave.encode(), bytes.fromhex(sal_hex), _ITERACIONES)
    # compare_digest evita ataques de temporización.
    return hmac.compare_digest(digest.hex(), hash_hex)


# ---------- JWT ----------
def crear_token(usuario: Usuario) -> str:
    payload = {
        "sub": str(usuario.id),
        "rol": usuario.rol.value,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.token_horas),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


_bearer = HTTPBearer(auto_error=False)


def usuario_actual(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    """Dependencia: obtiene el usuario autenticado o responde 401."""
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No autenticado")
    try:
        payload = jwt.decode(cred.credentials, settings.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o vencido")
    usuario = db.get(Usuario, int(payload["sub"]))
    if usuario is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario no existe")
    return usuario


def solo_coordinador(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
    """Dependencia: exige rol coordinador."""
    if usuario.rol != Rol.COORDINADOR:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo el coordinador puede hacer esto")
    return usuario
