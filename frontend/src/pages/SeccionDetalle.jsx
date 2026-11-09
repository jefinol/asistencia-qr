// Dashboard de una sección: estadísticas, clases, estudiantes, reportes.
// Lo usan el docente (para su sección) y el coordinador (al escoger una sección).
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, descargar } from '../api.js'
import { useAuth } from '../auth.jsx'
import { Error, GraficoAsistencia, Porcentaje, Tarjeta, useApi } from '../components.jsx'

export default function SeccionDetalle() {
  const { seccionId } = useParams()
  const { usuario } = useAuth()
  const navegar = useNavigate()
  const esCoordinador = usuario.rol === 'coordinador'
  const { datos: est, error, recargar } = useApi(`/secciones/${seccionId}/estadisticas`)
  const [tema, setTema] = useState('')
  const [aviso, setAviso] = useState('')

  if (error) return <Error texto={error} />
  if (!est) return <p>Cargando…</p>
  const r = est.resumen

  // Envuelve una acción async mostrando su error (si lo hay) y recargando los datos.
  const accion = (fn) => async (...args) => {
    setAviso('')
    try {
      await fn(...args)
      recargar()
    } catch (e) {
      setAviso(e.message)
    }
  }

  const iniciarClase = accion(async (e) => {
    e.preventDefault()
    const clase = await api(`/secciones/${seccionId}/clases`, { method: 'POST', body: { tema } })
    navegar(`/clases/${clase.id}/proyectar`)
  })

  const eliminarSeccion = accion(async () => {
    if (!confirm(`¿Eliminar la sección ${r.codigo} con todas sus clases y asistencias?`)) return
    await api(`/secciones/${seccionId}`, { method: 'DELETE' })
    navegar('/')
  })

  return (
    <>
      <div className="encabezado">
        <div>
          <h1>{r.codigo} · {r.asignatura}</h1>
          <p className="tenue">Docente: {r.docente ?? 'sin asignar'}</p>
        </div>
        <div className="botones">
          <button onClick={accion(() => descargar(`/secciones/${seccionId}/reporte?formato=pdf`))}>⬇ PDF</button>
          <button onClick={accion(() => descargar(`/secciones/${seccionId}/reporte?formato=excel`))}>⬇ Excel</button>
          {esCoordinador && <button className="peligro" onClick={eliminarSeccion}>Eliminar sección</button>}
        </div>
      </div>
      <Error texto={aviso} />

      <div className="tarjetas">
        <Tarjeta titulo="Estudiantes" valor={r.total_estudiantes} />
        <Tarjeta titulo="Clases" valor={r.total_clases} />
        <Tarjeta titulo="Asistencia promedio" valor={`${r.promedio_asistencia}%`} />
        <Tarjeta titulo="En riesgo (<75%)" valor={r.estudiantes_en_riesgo} alerta={r.estudiantes_en_riesgo > 0} />
      </div>

      <section className="panel">
        <h2>Iniciar clase</h2>
        <form className="fila" onSubmit={iniciarClase}>
          <input placeholder="Tema de hoy (opcional)" value={tema} onChange={(e) => setTema(e.target.value)} />
          <button className="primario" disabled={!r.total_estudiantes}>Iniciar y proyectar QR</button>
        </form>
        {!r.total_estudiantes && <p className="tenue">Primero hay que cargar la matrícula.</p>}
      </section>

      <section className="panel">
        <h2>Asistencia por clase</h2>
        <GraficoAsistencia datos={est.clases.map((c) => ({ nombre: c.fecha.slice(5), porcentaje: c.porcentaje }))} />
        <Clases clases={est.clases} accion={accion} navegar={navegar} />
      </section>

      <section className="panel">
        <h2>Estudiantes</h2>
        {esCoordinador && <CargarMatricula seccionId={seccionId} alCargar={recargar} />}
        <Estudiantes lista={est.estudiantes} esCoordinador={esCoordinador}
          retirar={accion(async (e) => {
            if (!confirm(`¿Retirar a ${e.nombres} ${e.apellidos} de la sección?`)) return
            await api(`/secciones/${seccionId}/estudiantes/${e.estudiante_id}`, { method: 'DELETE' })
          })} />
      </section>
    </>
  )
}

function Clases({ clases, accion, navegar }) {
  if (!clases.length) return null
  return (
    <table>
      <thead><tr><th>Fecha</th><th>Tema</th><th>Presentes</th><th>%</th><th>Estado</th><th></th></tr></thead>
      <tbody>
        {[...clases].reverse().map((c) => (
          <tr key={c.clase_id}>
            <td>{c.fecha}</td>
            <td>{c.tema || <span className="tenue">—</span>}</td>
            <td>{c.presentes}</td>
            <td><Porcentaje valor={c.porcentaje} /></td>
            <td>{c.abierta ? <span className="etiqueta verde">Abierta</span> : <span className="etiqueta">Cerrada</span>}</td>
            <td className="botones">
              <button onClick={() => navegar(`/clases/${c.clase_id}/proyectar`)}>{c.abierta ? 'Proyectar' : 'Ver lista'}</button>
              {c.abierta
                ? <button onClick={accion(() => api(`/clases/${c.clase_id}/cerrar`, { method: 'POST' }))}>Cerrar</button>
                : <button onClick={accion(() => api(`/clases/${c.clase_id}/reabrir`, { method: 'POST' }))}>Reabrir</button>}
              <button className="peligro" onClick={accion(async () => {
                if (confirm('¿Eliminar esta clase y sus asistencias?'))
                  await api(`/clases/${c.clase_id}`, { method: 'DELETE' })
              })}>✕</button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function Estudiantes({ lista, esCoordinador, retirar }) {
  const [filtro, setFiltro] = useState('')
  const f = filtro.toLowerCase()
  const visibles = lista.filter((e) => `${e.cedula} ${e.nombres} ${e.apellidos}`.toLowerCase().includes(f))
  if (!lista.length) return <p className="tenue">Sin estudiantes inscritos.</p>
  return (
    <>
      <input className="buscador" placeholder="Buscar por nombre o cédula…" value={filtro} onChange={(e) => setFiltro(e.target.value)} />
      <table>
        <thead><tr><th>Cédula</th><th>Apellidos</th><th>Nombres</th><th>Asist.</th><th>Inasist.</th><th>%</th>{esCoordinador && <th></th>}</tr></thead>
        <tbody>
          {visibles.map((e) => (
            <tr key={e.estudiante_id} className={e.en_riesgo ? 'riesgo' : ''}>
              <td>{e.cedula}</td><td>{e.apellidos}</td><td>{e.nombres}</td>
              <td>{e.asistencias}</td><td>{e.inasistencias}</td>
              <td><Porcentaje valor={e.porcentaje} /></td>
              {esCoordinador && <td><button className="enlace" onClick={() => retirar(e)}>Retirar</button></td>}
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}

function CargarMatricula({ seccionId, alCargar }) {
  const [resultado, setResultado] = useState(null)
  const [error, setError] = useState('')

  async function subir(e) {
    const archivo = e.target.files[0]
    if (!archivo) return
    setError('')
    setResultado(null)
    const form = new FormData()
    form.append('archivo', archivo)
    try {
      setResultado(await api(`/secciones/${seccionId}/matricula`, { method: 'POST', form }))
      alCargar()
    } catch (err) {
      setError(err.message)
    }
    e.target.value = '' // permite volver a subir el mismo archivo
  }

  return (
    <div className="matricula">
      <label className="boton-archivo">
        ⬆ Cargar matrícula (CSV o Excel)
        <input type="file" accept=".csv,.xlsx" onChange={subir} hidden />
      </label>
      <span className="tenue">Columnas: <code>nombres, apellidos, cedula</code></span>
      <Error texto={error} />
      {resultado && (
        <p className="exito">
          {resultado.agregados} agregados, {resultado.ya_inscritos} ya estaban inscritos.
          {resultado.errores.length > 0 && <><br />Avisos: {resultado.errores.join(' · ')}</>}
        </p>
      )}
    </div>
  )
}
