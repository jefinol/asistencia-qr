// Cliente HTTP mínimo sobre fetch. Todas las llamadas a la API pasan por aquí,
// así el token y el manejo de errores están en un solo lugar.

const CLAVE_TOKEN = 'asistencia_token'

export const tokenGuardado = {
  leer: () => localStorage.getItem(CLAVE_TOKEN),
  guardar: (t) => localStorage.setItem(CLAVE_TOKEN, t),
  borrar: () => localStorage.removeItem(CLAVE_TOKEN),
}

/** Convierte el "detail" de FastAPI (texto o lista de errores de validación) en un mensaje legible. */
function mensajeDeError(cuerpo, status) {
  const d = cuerpo?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((e) => `${e.loc?.at(-1)}: ${e.msg}`).join('; ')
  return `Error ${status}`
}

export async function api(ruta, { method = 'GET', body, form } = {}) {
  const headers = {}
  const token = tokenGuardado.leer()
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  const resp = await fetch(`/api${ruta}`, {
    method,
    headers,
    body: form ?? (body !== undefined ? JSON.stringify(body) : undefined),
  })
  if (resp.status === 401 && token) {
    tokenGuardado.borrar()
    window.location.href = '/login'
  }
  if (resp.status === 204) return null
  const cuerpo = await resp.json().catch(() => null)
  if (!resp.ok) throw new Error(mensajeDeError(cuerpo, resp.status))
  return cuerpo
}

/** Descarga un archivo (PDF/Excel) respetando el token. */
export async function descargar(ruta) {
  const resp = await fetch(`/api${ruta}`, {
    headers: { Authorization: `Bearer ${tokenGuardado.leer()}` },
  })
  if (!resp.ok) throw new Error('No se pudo generar el reporte')
  const nombre = resp.headers.get('Content-Disposition')?.match(/filename="(.+)"/)?.[1] ?? 'reporte'
  const url = URL.createObjectURL(await resp.blob())
  const a = Object.assign(document.createElement('a'), { href: url, download: nombre })
  a.click()
  URL.revokeObjectURL(url)
}
