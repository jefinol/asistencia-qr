// Componentes reutilizables pequeños.
import { useCallback, useEffect, useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from './api.js'
import { useAuth } from './auth.jsx'

export const UMBRAL_RIESGO = 75 // debe coincidir con backend/app/services/estadisticas.py

/** Hook: carga datos de la API y expone {datos, error, recargar}. */
export function useApi(ruta) {
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState('')
  const recargar = useCallback(() => {
    api(ruta).then(setDatos).catch((e) => setError(e.message))
  }, [ruta])
  useEffect(recargar, [recargar])
  return { datos, error, recargar }
}

export function Layout() {
  const { usuario, salir } = useAuth()
  return (
    <>
      <header className="barra">
        <Link to="/" className="marca">▣ Asistencia QR</Link>
        <nav>
          <NavLink to="/" end>Inicio</NavLink>
          {usuario.rol === 'coordinador' && <NavLink to="/docentes">Docentes</NavLink>}
        </nav>
        <span className="usuario">
          {usuario.nombre} · <em>{usuario.rol}</em>
          <button className="enlace" onClick={salir}>Salir</button>
        </span>
      </header>
      <main className="contenido"><Outlet /></main>
    </>
  )
}

export function Tarjeta({ titulo, valor, alerta }) {
  return (
    <div className={`tarjeta ${alerta ? 'alerta' : ''}`}>
      <span>{titulo}</span>
      <strong>{valor}</strong>
    </div>
  )
}

export function Error({ texto }) {
  return texto ? <p className="error">{texto}</p> : null
}

/** Barras de % de asistencia; rojo si está bajo el umbral. `datos` = [{nombre, porcentaje}] */
export function GraficoAsistencia({ datos, alto = 260 }) {
  if (!datos.length) return <p className="tenue">Aún no hay datos para graficar.</p>
  return (
    <ResponsiveContainer width="100%" height={alto}>
      <BarChart data={datos} margin={{ top: 10, right: 10, bottom: 0, left: -20 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="nombre" fontSize={12} />
        <YAxis domain={[0, 100]} unit="%" fontSize={12} />
        <Tooltip formatter={(v) => `${v}%`} />
        <ReferenceLine y={UMBRAL_RIESGO} stroke="#c0392b" strokeDasharray="4 4" />
        <Bar dataKey="porcentaje" radius={[4, 4, 0, 0]}>
          {datos.map((d, i) => (
            <Cell key={i} fill={d.porcentaje < UMBRAL_RIESGO ? '#e07a6f' : '#3b7ddd'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function Porcentaje({ valor }) {
  return <span className={valor < UMBRAL_RIESGO ? 'pct bajo' : 'pct'}>{valor}%</span>
}
