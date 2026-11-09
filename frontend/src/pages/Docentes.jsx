// Gestión de docentes (solo coordinador).
import { useState } from 'react'
import { api } from '../api.js'
import { Error, useApi } from '../components.jsx'

export default function Docentes() {
  const { datos: docentes, recargar } = useApi('/docentes')
  const vacio = { usuario: '', nombre: '', clave: '' }
  const [form, setForm] = useState(vacio)
  const [error, setError] = useState('')

  async function enviar(e) {
    e.preventDefault()
    setError('')
    try {
      await api('/docentes', { method: 'POST', body: form })
      setForm(vacio)
      recargar()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <>
      <h1>Docentes</h1>
      <section className="panel">
        <h2>Registrar docente</h2>
        <form className="fila" onSubmit={enviar}>
          <input placeholder="Nombre completo" value={form.nombre} required
            onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
          <input placeholder="Usuario" value={form.usuario} required
            onChange={(e) => setForm({ ...form, usuario: e.target.value })} />
          <input placeholder="Clave (mín. 6)" type="password" value={form.clave} required
            onChange={(e) => setForm({ ...form, clave: e.target.value })} />
          <button className="primario">Registrar</button>
        </form>
        <Error texto={error} />
      </section>
      <section className="panel">
        <table>
          <thead><tr><th>Nombre</th><th>Usuario</th></tr></thead>
          <tbody>
            {docentes?.map((d) => <tr key={d.id}><td>{d.nombre}</td><td>{d.usuario}</td></tr>)}
          </tbody>
        </table>
      </section>
    </>
  )
}
