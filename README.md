# Asistencia QR

Sistema de control de asistencia por código QR. Proyecto final de Programación III.

- El **coordinador** crea secciones (código + asignatura), registra docentes y carga la matrícula (CSV/Excel).
- El **docente** inicia una clase y proyecta un QR que **cambia cada 30 s**.
- El **alumno** escanea el QR con su teléfono, escribe su cédula y queda marcado. No necesita cuenta.
- Docente y coordinador ven dashboards con porcentajes de asistencia y exportan reportes en **PDF** o **Excel**.

Las decisiones de diseño (por qué FastAPI, Vite, SQLite, cómo funciona el QR rotativo, estructuras de datos y algoritmos) están en [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md).

## Estructura

```
asistencia-qr/
├── backend/                 FastAPI (Python, gestionado con uv)
│   ├── app/
│   │   ├── main.py          punto de entrada; sirve la API y el frontend compilado
│   │   ├── config.py        variables de entorno
│   │   ├── database.py      conexión SQLAlchemy
│   │   ├── models.py        tablas (Usuario, Seccion, Estudiante, Inscripcion, Clase, Asistencia)
│   │   ├── schemas.py       JSON de entrada/salida (Pydantic)
│   │   ├── security.py      contraseñas, JWT, roles
│   │   ├── routers/         rutas HTTP (auth, secciones, clases)
│   │   └── services/        lógica de negocio: QR, matrícula, estadísticas, reportes
│   └── tests/               pruebas con pytest
├── frontend/                React + Vite
│   └── src/
│       ├── api.js           cliente HTTP
│       ├── auth.jsx         sesión del usuario
│       ├── components.jsx   piezas reutilizables (tarjetas, gráfico…)
│       └── pages/           Login, Inicio, SeccionDetalle, Proyectar, Asistir, Docentes
├── ejemplos/                archivo de matrícula de ejemplo
├── docs/ARQUITECTURA.md
├── Dockerfile               imagen única (build de React + backend)
└── docker-compose.yml
```

## Desarrollo local

Requisitos: [uv](https://docs.astral.sh/uv/), Node 20+.

**Backend** (terminal 1):

```bash
cd backend
```

```bash
uv sync
```

```bash
uv run uvicorn app.main:app --reload
```

API en http://localhost:8000 · documentación interactiva en http://localhost:8000/docs

**Frontend** (terminal 2):

```bash
cd frontend
```

```bash
npm install
```

```bash
npm run dev
```

Abrir http://localhost:5173. Usuario inicial: `coordinador` / `coordinador123` (se cambia con `ADMIN_USUARIO` / `ADMIN_CLAVE`).

> **Probar el QR con un teléfono:** el teléfono debe poder abrir el enlace. Abre el frontend usando la IP de tu computadora en la red Wi-Fi (Vite la muestra como "Network", p. ej. `http://192.168.1.20:5173`) en lugar de `localhost`.

**Pruebas:**

```bash
cd backend && uv run pytest
```

## Despliegue en un VPS (Docker)

```bash
cp .env.example .env
```

Editar `.env` (sobre todo `SECRET_KEY` y `ADMIN_CLAVE`) y luego:

```bash
docker compose up -d --build
```

La app queda en el puerto 8000. La base de datos vive en el volumen `datos`, así que sobrevive a reinicios.

Recomendado: poner delante un proxy con HTTPS (Caddy o Nginx). Con Caddy basta un `Caddyfile` así:

```
asistencia.midominio.com {
    reverse_proxy localhost:8000
}
```

**Respaldo de la base de datos:**

```bash
docker compose cp app:/app/data/asistencia.db ./respaldo.db
```

## Flujo de uso

1. Entrar como coordinador → **Docentes** → registrar a los profesores.
2. **Inicio** → *Nueva sección* (código, asignatura, docente).
3. Abrir la sección → **Cargar matrícula** (ver `ejemplos/matricula_ejemplo.csv`; columnas `nombres, apellidos, cedula`).
4. El docente entra, abre su sección → **Iniciar y proyectar QR**.
5. Los alumnos escanean, ponen su cédula y el contador sube en vivo. Quien no tenga teléfono se marca con **Pasar lista manual**.
6. **Cerrar clase**. Las estadísticas y reportes se actualizan solos.
