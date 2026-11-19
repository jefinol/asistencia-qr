// "Mi cuenta": cualquier usuario (docente o coordinador) cambia su propia clave.
import { useState } from 'react'
import { api } from '../api.js'
import { useAuth } from '../auth.jsx'
import { Error } from '../components.jsx'

export default function Cuenta() {
  const { usuario } = useAuth()
  const vacio = { clave_actual: '', clave_nueva: '', repetir: '' }
  const [form, setForm] = useState(vacio)
  const [error, setError] = useState('')
  const [listo, setListo] = useState(false)
  const cambiar = (campo) => (e) => setForm({ ...form, [campo]: e.target.value })

  async function enviar(e) {
    e.preventDefault()
    setError('')
    setListo(false)
    if (form.clave_nueva !== form.repetir) return setError('Las claves nuevas no coinciden')
    try {
      await api('/auth/clave', {
        method: 'PUT', body: { clave_actual: form.clave_actual, clave_nueva: form.clave_nueva },
      })
      setForm(vacio)
      setListo(true)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <>
      <h1>Mi cuenta</h1>
      <p className="tenue">{usuario.nombre} · usuario <code>{usuario.usuario}</code> · {usuario.rol}</p>
      <section className="panel angosto">
        <h2>Cambiar clave</h2>
        <form className="columna" onSubmit={enviar}>
          <label>Clave actual
            <input type="password" required value={form.clave_actual} onChange={cambiar('clave_actual')} />
          </label>
          <label>Clave nueva (mín. 6)
            <input type="password" required minLength={6} value={form.clave_nueva} onChange={cambiar('clave_nueva')} />
          </label>
          <label>Repetir clave nueva
            <input type="password" required minLength={6} value={form.repetir} onChange={cambiar('repetir')} />
          </label>
          <Error texto={error} />
          {listo && <p className="exito">Clave actualizada.</p>}
          <button className="primario">Guardar</button>
        </form>
      </section>
    </>
  )
}
