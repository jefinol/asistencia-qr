"""Algoritmo del código rotativo del QR.

Problema: si el QR fuera fijo, un alumno podría tomarle foto y mandarla por
WhatsApp a quien no vino. Solución (misma idea que TOTP, los códigos de 6
dígitos de Google Authenticator):

    ventana  = floor(tiempo_actual / N segundos)
    código   = HMAC-SHA256(secreto_de_la_clase, clase_id:ventana)  → 8 caracteres

- El docente proyecta un QR cuyo enlace incluye el código de la ventana actual;
  el frontend pide uno nuevo cada N segundos, así que el QR "cambia solo".
- El servidor no guarda los códigos: los RECALCULA y compara. Acepta la ventana
  actual y la anterior para tolerar al alumno que escaneó justo en el borde.

Complejidad: O(1) en tiempo y memoria por verificación.
"""
import hashlib
import hmac
import time


class GeneradorCodigoQR:
    def __init__(self, ventana_segundos: int = 30, ventanas_tolerancia: int = 1):
        self.ventana_segundos = ventana_segundos
        self.ventanas_tolerancia = ventanas_tolerancia

    def _ventana(self, instante: float | None = None) -> int:
        return int((instante if instante is not None else time.time()) // self.ventana_segundos)

    @staticmethod
    def _calcular(secreto: str, clase_id: int, ventana: int) -> str:
        mensaje = f"{clase_id}:{ventana}".encode()
        return hmac.new(secreto.encode(), mensaje, hashlib.sha256).hexdigest()[:8]

    def generar(self, secreto: str, clase_id: int, instante: float | None = None) -> str:
        """Código vigente para la clase en este momento."""
        return self._calcular(secreto, clase_id, self._ventana(instante))

    def segundos_restantes(self, instante: float | None = None) -> int:
        """Cuánto le queda al código actual (para que el frontend sepa cuándo refrescar)."""
        t = instante if instante is not None else time.time()
        return self.ventana_segundos - int(t % self.ventana_segundos)

    def es_valido(self, secreto: str, clase_id: int, codigo: str, instante: float | None = None) -> bool:
        """True si `codigo` corresponde a la ventana actual o a las anteriores toleradas."""
        actual = self._ventana(instante)
        for v in range(actual - self.ventanas_tolerancia, actual + 1):
            if hmac.compare_digest(self._calcular(secreto, clase_id, v), codigo):
                return True
        return False
