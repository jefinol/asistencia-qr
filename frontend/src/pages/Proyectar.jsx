// Pantalla para el proyector: QR grande que se renueva solo + contador de presentes.
// También permite pasar lista manual (alumno sin teléfono).
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { QRCodeSVG } from 'qrcode.react'
import { api } from '../api.js'
import { Error } from '../components.jsx'

const REFRESCO_MS = 2000 // cada cuánto preguntamos al backend (código vigente y presentes)

export default function Proyectar() {
  const { claseId } = useParams()
  const [info, setInfo] = useState(null)
  const [qr, setQr] = useState(null)
  const [lista, setLista] = useState(null)
  const [verLista, setVerLista] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api(`/publico/clases/${claseId}`).then(setInfo).catch((e) => setError(e.message))
    api(`/clases/${claseId}`).then((c) => setInfo((i) => ({ ...i, seccion_id: c.seccion_id })))
  }, [claseId])

  // Sondeo periódico: el backend decide qué código es el vigente (ver services/codigo_qr.py).
  useEffect(() => {
    const consultar = () => api(`/clases/${claseId}/qr`).then(setQr).catch((e) => setError(e.message))
    consultar()
    const id = setInterval(consultar, REFRESCO_MS)
    return () => clearInterval(id)
  }, [claseId])

  const cargarLista = () => api(`/clases/${claseId}/asistentes`).then(setLista)
  useEffect(() => { if (verLista) cargarLista() }, [verLista, qr?.presentes])

  async function alternar(estudianteId) {
    await api(`/clases/${claseId}/asistentes/${estudianteId}`, { method: 'PUT' })
    cargarLista()
  }

  async function cerrar() {
    await api(`/clases/${claseId}/cerrar`, { method: 'POST' })
    setQr({ ...qr, abierta: false })
  }

  if (error) return <div className="contenido"><Error texto={error} /></div>
  if (!qr || !info) return <p className="centro">Cargando…</p>

  const enlace = `${window.location.origin}/asistir/${claseId}?c=${qr.codigo}`
  const esLocal = ['localhost', '127.0.0.1'].includes(window.location.hostname)

  return (
    <div className="proyector">
      <div className="proyector-qr">
        <h1>{info.asignatura}</h1>
        <p className="tenue">Sección {info.seccion} · {info.fecha}{info.tema && ` · ${info.tema}`}</p>
        {qr.abierta ? (
          <>
            <div className="qr-marco"><QRCodeSVG value={enlace} size={360} marginSize={2} /></div>
            <p>Escanea con tu teléfono e ingresa tu cédula</p>
            <p className="tenue">El código cambia en {qr.segundos_restantes}s</p>
            {esLocal && (
              <p className="error">Estás en "localhost": los teléfonos no podrán abrir el enlace.
                Abre esta página usando la IP de la computadora o el dominio del servidor.</p>
            )}
          </>
        ) : <p className="cerrada">Clase cerrada</p>}
      </div>
      <aside className="proyector-lado">
        <div className="contador"><strong>{qr.presentes}</strong> / {qr.inscritos}<span>presentes</span></div>
        <div className="botones columna">
          {qr.abierta && <button className="peligro" onClick={cerrar}>Cerrar clase</button>}
          <button onClick={() => setVerLista(!verLista)}>{verLista ? 'Ocultar lista' : 'Pasar lista manual'}</button>
          {info.seccion_id && <Link className="boton" to={`/secciones/${info.seccion_id}`}>← Volver a la sección</Link>}
        </div>
        {verLista && lista && (
          <ul className="lista-manual">
            {lista.map((a) => (
              <li key={a.estudiante_id}>
                <label>
                  <input type="checkbox" checked={a.presente} onChange={() => alternar(a.estudiante_id)} />
                  {a.nombre} <span className="tenue">{a.cedula}</span>
                </label>
              </li>
            ))}
          </ul>
        )}
      </aside>
    </div>
  )
}
