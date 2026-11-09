// Contexto de autenticación: guarda quién inició sesión y lo comparte con toda la app.
import { createContext, useContext, useEffect, useState } from 'react'
import { api, tokenGuardado } from './api.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  const [cargando, setCargando] = useState(Boolean(tokenGuardado.leer()))

  // Al recargar la página, si hay token guardado recuperamos el usuario.
  useEffect(() => {
    if (!tokenGuardado.leer()) return
    api('/auth/yo')
      .then(setUsuario)
      .catch(() => tokenGuardado.borrar())
      .finally(() => setCargando(false))
  }, [])

  async function entrar(nombreUsuario, clave) {
    const r = await api('/auth/login', { method: 'POST', body: { usuario: nombreUsuario, clave } })
    tokenGuardado.guardar(r.token)
    setUsuario(r.usuario)
    return r.usuario
  }

  function salir() {
    tokenGuardado.borrar()
    setUsuario(null)
  }

  return (
    <AuthContext.Provider value={{ usuario, cargando, entrar, salir }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
