// Página PÚBLICA que abre el alumno al escanear el QR. No requiere cuenta:
// solo escribe su cédula. Pensada para pantalla de teléfono.
import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api.js'
import { Error } from '../components.jsx'

export default function Asistir() {
  const { claseId } = useParams()
  const [params] = useSearchParams()
  const codigo = params.get('c') ?? ''
  const [info, setInfo] = useState(null)
  const [cedula, setCedula] = useState('')
  const [resultado, setResultado] = useState(null)
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    api(`/publico/clases/${claseId}?c=${encodeURIComponent(codigo)}`).then(setInfo).catch((e) => setError(e.message))
  }, [claseId, codigo])

  async function enviar(e) {
    e.preventDefault()
    setError('')
    setEnviando(true)
    try {
      setResultado(await api('/publico/asistencia', {
        method: 'POST', body: { clase_id: Number(claseId), codigo, cedula },
      }))
    } catch (err) {
      setError(err.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="pantalla-centro">
      <div className="caja">
        <h1>▣ Asistencia</h1>
        {info && (
          <p><strong>{info.asignatura}</strong><br /><span className="tenue">Sección {info.seccion} · {info.fecha}</span></p>
        )}
        {resultado ? (
          <div className="exito grande">
            <p>✔ {resultado.mensaje}</p>
            <p>{resultado.estudiante}</p>
          </div>
        ) : info && !info.codigo_valido ? (
          <Error texto="Este código QR expiró o la clase ya cerró. Vuelve a escanear el código proyectado." />
        ) : info && (
          <form onSubmit={enviar}>
            <label>Tu cédula
              <input inputMode="numeric" autoFocus required placeholder="Ej. 28123456"
                value={cedula} onChange={(e) => setCedula(e.target.value)} />
            </label>
            <button className="primario" disabled={enviando}>{enviando ? 'Enviando…' : 'Marcar asistencia'}</button>
          </form>
        )}
        <Error texto={error} />
      </div>
    </div>
  )
}
