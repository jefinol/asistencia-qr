// Página de inicio. Muestra algo distinto según el rol:
//   - Coordinador: estadísticas generales + gestión de secciones.
//   - Docente: sus secciones con su % de asistencia.
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import { useAuth } from '../auth.jsx'
import { Error, GraficoAsistencia, Porcentaje, Tarjeta, useApi } from '../components.jsx'

export default function Inicio() {
  const { usuario } = useAuth()
  return usuario.rol === 'coordinador' ? <InicioCoordinador /> : <InicioDocente />
}

function TablaSecciones({ secciones }) {
  if (!secciones.length) return <p className="tenue">No hay secciones todavía.</p>
  return (
    <table>
      <thead>
        <tr><th>Código</th><th>Asignatura</th><th>Docente</th><th>Estudiantes</th><th>Clases</th><th>Asistencia</th><th>En riesgo</th></tr>
      </thead>
      <tbody>
        {secciones.map((s) => (
          <tr key={s.seccion_id}>
            <td><Link to={`/secciones/${s.seccion_id}`}>{s.codigo}</Link></td>
            <td>{s.asignatura}</td>
            <td>{s.docente ?? <span className="tenue">Sin asignar</span>}</td>
            <td>{s.total_estudiantes}</td>
            <td>{s.total_clases}</td>
            <td><Porcentaje valor={s.promedio_asistencia} /></td>
            <td>{s.estudiantes_en_riesgo}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function InicioCoordinador() {
  const { datos, error, recargar } = useApi('/estadisticas/general')
  if (error) return <Error texto={error} />
  if (!datos) return <p>Cargando…</p>
  return (
    <>
      <h1>Panel del coordinador</h1>
      <div className="tarjetas">
        <Tarjeta titulo="Secciones" valor={datos.total_secciones} />
        <Tarjeta titulo="Inscripciones" valor={datos.total_estudiantes} />
        <Tarjeta titulo="Clases dictadas" valor={datos.total_clases} />
        <Tarjeta titulo="Asistencia promedio" valor={`${datos.promedio_asistencia}%`} />
      </div>
      <section className="panel">
        <h2>Asistencia por sección</h2>
        <GraficoAsistencia datos={datos.secciones.map((s) => ({ nombre: s.codigo, porcentaje: s.promedio_asistencia }))} />
      </section>
      <section className="panel">
        <h2>Secciones</h2>
        <TablaSecciones secciones={datos.secciones} />
      </section>
      <NuevaSeccion alCrear={recargar} />
    </>
  )
}

function NuevaSeccion({ alCrear }) {
  const { datos: docentes } = useApi('/docentes')
  const vacio = { codigo: '', asignatura: '', docente_id: '' }
  const [form, setForm] = useState(vacio)
  const [error, setError] = useState('')

  async function enviar(e) {
    e.preventDefault()
    setError('')
    try {
      await api('/secciones', {
        method: 'POST',
        body: { ...form, docente_id: form.docente_id ? Number(form.docente_id) : null },
      })
      setForm(vacio)
      alCrear()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="panel">
      <h2>Nueva sección</h2>
      <form className="fila" onSubmit={enviar}>
        <input placeholder="Código (ej. 301A)" value={form.codigo} required
          onChange={(e) => setForm({ ...form, codigo: e.target.value })} />
        <input placeholder="Asignatura" value={form.asignatura} required
          onChange={(e) => setForm({ ...form, asignatura: e.target.value })} />
        <select value={form.docente_id} onChange={(e) => setForm({ ...form, docente_id: e.target.value })}>
          <option value="">— Docente —</option>
          {docentes?.map((d) => <option key={d.id} value={d.id}>{d.nombre}</option>)}
        </select>
        <button className="primario">Crear</button>
      </form>
      <Error texto={error} />
    </section>
  )
}

function InicioDocente() {
  const { datos: secciones, error } = useApi('/secciones')
  if (error) return <Error texto={error} />
  if (!secciones) return <p>Cargando…</p>
  return (
    <>
      <h1>Mis secciones</h1>
      {!secciones.length && <p className="tenue">El coordinador aún no te ha asignado secciones.</p>}
      <div className="tarjetas">
        {secciones.map((s) => (
          <Link key={s.id} to={`/secciones/${s.id}`} className="tarjeta enlace-tarjeta">
            <span>{s.codigo}</span>
            <strong className="mediano">{s.asignatura}</strong>
          </Link>
        ))}
      </div>
    </>
  )
}
