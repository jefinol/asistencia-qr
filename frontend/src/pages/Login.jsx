import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth.jsx'
import { Error } from '../components.jsx'

export default function Login() {
  const { usuario, entrar } = useAuth()
  const navegar = useNavigate()
  const [form, setForm] = useState({ usuario: '', clave: '' })
  const [error, setError] = useState('')

  if (usuario) return <Navigate to="/" replace />

  async function enviar(e) {
    e.preventDefault()
    setError('')
    try {
      await entrar(form.usuario, form.clave)
      navegar('/')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="pantalla-centro">
      <form className="caja" onSubmit={enviar}>
        <h1>▣ Asistencia QR</h1>
        <p className="tenue">Acceso para coordinadores y docentes</p>
        <label>Usuario
          <input autoFocus value={form.usuario} onChange={(e) => setForm({ ...form, usuario: e.target.value })} />
        </label>
        <label>Clave
          <input type="password" value={form.clave} onChange={(e) => setForm({ ...form, clave: e.target.value })} />
        </label>
        <Error texto={error} />
        <button className="primario">Entrar</button>
      </form>
    </div>
  )
}
