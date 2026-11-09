// Rutas de la aplicación.
//   Públicas : /login, /asistir/:claseId (la que abre el alumno al escanear)
//   Privadas : el resto, protegidas por <Privada>
import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth.jsx'
import { Layout } from './components.jsx'
import Login from './pages/Login.jsx'
import Inicio from './pages/Inicio.jsx'
import Docentes from './pages/Docentes.jsx'
import SeccionDetalle from './pages/SeccionDetalle.jsx'
import Proyectar from './pages/Proyectar.jsx'
import Asistir from './pages/Asistir.jsx'

function Privada({ children, rol }) {
  const { usuario, cargando } = useAuth()
  if (cargando) return <p className="centro">Cargando…</p>
  if (!usuario) return <Navigate to="/login" replace />
  if (rol && usuario.rol !== rol) return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/asistir/:claseId" element={<Asistir />} />
      <Route path="/clases/:claseId/proyectar" element={<Privada><Proyectar /></Privada>} />
      <Route element={<Privada><Layout /></Privada>}>
        <Route path="/" element={<Inicio />} />
        <Route path="/secciones/:seccionId" element={<SeccionDetalle />} />
        <Route path="/docentes" element={<Privada rol="coordinador"><Docentes /></Privada>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
