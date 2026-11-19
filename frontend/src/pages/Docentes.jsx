// Gestión de docentes (solo coordinador): registrar, editar nombre, reiniciar
// claves olvidadas y eliminar. El coordinador NO crea otros coordinadores
// (fuera del alcance del MVP; ver docs/ARQUITECTURA.md).
import { useState } from 'react'
import { api } from '../api.js'
import { Error, useApi } from '../components.jsx'

export default function Docentes() {
  const { datos: docentes, recargar } = useApi('/docentes')
  const [aviso, setAviso] = useState('')

  return (
    <>
      <h1>Docentes</h1>
      <NuevoDocente alCrear={recargar} />
      <section className="panel">
        <h2>Registrados</h2>
        <Error texto={aviso} />
        {docentes && !docentes.length && <p className="tenue">Aún no hay docentes registrados.</p>}
        {docentes?.length > 0 && (
          <table>
            <thead><tr><th>Nombre</th><th>Usuario</th><th></th></tr></thead>
            <tbody>
              {docentes.map((d) => <FilaDocente key={d.id} d={d} alCambiar={recargar} setAviso={setAviso} />)}
            </tbody>
          </table>
        )}
      </section>
    </>
  )
}

function NuevoDocente({ alCrear }) {
  const vacio = { usuario: '', nombre: '', clave: '' }
  const [form, setForm] = useState(vacio)
  const [error, setError] = useState('')
  const cambiar = (campo) => (e) => setForm({ ...form, [campo]: e.target.value })

  async function enviar(e) {
    e.preventDefault()
    setError('')
    try {
      await api('/docentes', { method: 'POST', body: form })
      setForm(vacio)
      alCrear()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="panel">
      <h2>Registrar docente</h2>
      <form className="fila" onSubmit={enviar}>
        <input placeholder="Nombre completo" value={form.nombre} required onChange={cambiar('nombre')} />
        <input placeholder="Usuario" value={form.usuario} required onChange={cambiar('usuario')} />
        <input placeholder="Clave (mín. 6)" type="password" value={form.clave} required onChange={cambiar('clave')} />
        <button className="primario">Registrar</button>
      </form>
      <Error texto={error} />
    </section>
  )
}

/** Una fila de la tabla. Con "Editar" se convierte en un pequeño formulario. */
function FilaDocente({ d, alCambiar, setAviso }) {
  const [editando, setEditando] = useState(false)
  const [nombre, setNombre] = useState(d.nombre)
  const [clave, setClave] = useState('')

  async function guardar(e) {
    e.preventDefault()
    setAviso('')
    try {
      // Si la clave queda vacía, el backend conserva la anterior.
      await api(`/docentes/${d.id}`, { method: 'PUT', body: { nombre, clave: clave || null } })
      setEditando(false)
      setClave('')
      alCambiar()
    } catch (err) {
      setAviso(err.message)
    }
  }

  async function eliminar() {
    if (!confirm(`¿Eliminar a ${d.nombre}? Sus secciones quedarán sin docente asignado.`)) return
    setAviso('')
    try {
      await api(`/docentes/${d.id}`, { method: 'DELETE' })
      alCambiar()
    } catch (err) {
      setAviso(err.message)
    }
  }

  if (editando) {
    return (
      <tr>
        <td colSpan={3}>
          <form className="fila" onSubmit={guardar}>
            <input value={nombre} required minLength={3} onChange={(e) => setNombre(e.target.value)} />
            <input type="password" placeholder="Nueva clave (vacío = no cambiar)" minLength={6}
              value={clave} onChange={(e) => setClave(e.target.value)} />
            <button className="primario">Guardar</button>
            <button type="button" onClick={() => setEditando(false)}>Cancelar</button>
          </form>
        </td>
      </tr>
    )
  }

  return (
    <tr>
      <td>{d.nombre}</td>
      <td>{d.usuario}</td>
      <td className="botones">
        <button onClick={() => setEditando(true)}>Editar / clave</button>
        <button className="peligro" onClick={eliminar}>Eliminar</button>
      </td>
    </tr>
  )
}
