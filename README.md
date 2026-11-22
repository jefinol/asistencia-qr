# Asistencia QR

Sistema de control de asistencia por código QR. Proyecto final de Programación III.

- El **coordinador** crea y edita secciones (código + asignatura + docente), gestiona a los docentes (incluido reiniciar claves olvidadas) y carga la matrícula (CSV/Excel). No inicia clases ni proyecta el QR.
- El **docente** (y solo él) inicia una clase y proyecta un QR que **cambia cada 30 s**.
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
│       └── pages/           Login, Inicio, SeccionDetalle, Proyectar, Asistir, Docentes, Cuenta
├── ejemplos/                archivo de matrícula de ejemplo
├── docs/ARQUITECTURA.md
├── api/index.py             entrada de la API en Vercel (reutiliza backend/app)
├── vercel.json              configuración de despliegue en Vercel
├── requirements.txt         dependencias Python para Vercel (generado con uv)
├── Dockerfile               imagen única para desarrollo/VPS (build de React + backend)
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

API en http://localhost:8000 · documentación interactiva en http://localhost:8000/api/docs

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

**Pruebas contra PostgreSQL** (el mismo motor de Supabase). Levanta un Postgres desechable y apunta las pruebas a él. **Nunca** uses la base de producción: las pruebas la vacían.

```bash
docker run -d --rm --name pg-test -e POSTGRES_PASSWORD=test -p 55432:5432 postgres:16-alpine
```

```bash
cd backend && TEST_DATABASE_URL=postgresql://postgres:test@localhost:55432/postgres uv run pytest
```

## Despliegue en Vercel + Supabase (plan gratuito)

```
Navegador ──► Vercel ─┬─ CDN: frontend React (frontend/dist)
                      └─ /api/* ─► función Python (api/index.py → backend/app)
                                            │
                                            ▼
                              Supabase (PostgreSQL, pooler puerto 6543)
```

Archivos que lo hacen posible (ya están en el repo):

| Archivo | Para qué |
|---|---|
| `vercel.json` | Compila el frontend con Vite, manda `/api/*` a la función Python y el resto a `index.html`. |
| `api/index.py` | Función serverless: importa la misma app FastAPI de `backend/app/`. |
| `requirements.txt` | Dependencias de Python que instala Vercel (generado desde `backend/uv.lock`). |

### 1. Crear la base de datos en Supabase

1. Entra a https://supabase.com y crea un proyecto en el plan **Free**. Como región, elige **East US (North Virginia)**, que es donde Vercel ejecuta las funciones por defecto, para que la API responda más rápido. Guarda la contraseña de la base de datos que te pide.
2. En el proyecto, pulsa **Connect** y copia la cadena del **Transaction pooler**: la que usa el puerto **6543** y el host `...pooler.supabase.com`. Reemplaza `[YOUR-PASSWORD]` por tu contraseña. Tendrá esta forma:

   ```
   postgresql://postgres.<ref>:<contraseña>@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```

   No uses la "Direct connection": en el plan gratuito solo funciona por IPv6 y Vercel no puede alcanzarla.

No hace falta crear tablas: la app las crea sola en la primera petición, junto con el usuario coordinador.

### 2. Crear el proyecto en Vercel

1. Entra a https://vercel.com, pulsa **Add New → Project** e importa el repositorio de GitHub `asistencia-qr`.
2. Deja **Root Directory** en la raíz del repo. La configuración de build se toma de `vercel.json`, así que no hay que tocar nada más.
3. En **Environment Variables**, agrega:

   | Variable | Valor |
   |---|---|
   | `DATABASE_URL` | la cadena del pooler de Supabase (paso 1) |
   | `SECRET_KEY` | una clave larga y aleatoria (comando abajo) |
   | `ADMIN_USUARIO` | `coordinador` (o el que prefieran) |
   | `ADMIN_CLAVE` | la clave inicial del coordinador |
   | `ZONA_HORARIA` | `America/Caracas` |

   Para generar la `SECRET_KEY`:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

4. Pulsa **Deploy**. Al terminar, Vercel te da una URL `https://<proyecto>.vercel.app` con HTTPS incluido. Entra con `ADMIN_USUARIO` / `ADMIN_CLAVE` y cambia la clave desde "Mi cuenta".

A partir de ahí, **cada `git push` a `main` vuelve a desplegar automáticamente**.

### Si cambian las dependencias de Python

Vercel lee `requirements.txt`, no `uv.lock`. Después de `uv add ...`, regenera el archivo:

```bash
cd backend && uv export --no-dev --no-hashes --no-emit-project --format requirements-txt -o ../requirements.txt
```

### Límites del plan gratuito que deben conocer

- **Supabase Free:** si el proyecto tiene poca actividad durante unos 7 días, Supabase puede pausarlo. Se reactiva desde su panel con un clic. Antes de la presentación, entren una vez para despertarlo. Mientras está pausado, la API responde con error en unos 10 segundos en vez de quedarse colgada.
- **Vercel Hobby:** es para proyectos personales y no comerciales, así que un proyecto académico encaja. La primera petición después de un rato sin uso tarda 1 o 2 segundos más (arranque en frío).
- **Proyector:** consulta la API cada 2 segundos mientras está abierto. Una clase de 90 minutos son unas 2.700 peticiones, muy por debajo de los límites del plan.

### Alternativa: un VPS con Docker

El mismo `docker compose up -d --build` de desarrollo sirve en un VPS, con SQLite en el volumen `datos`. Para tener HTTPS, pongan delante Caddy (`reverse_proxy localhost:8000`).

## Flujo de uso

1. Entrar como coordinador → **Docentes** → registrar a los profesores. Cada quien puede cambiar su clave haciendo clic en su nombre (arriba a la derecha); si un docente la olvida, el coordinador se la reinicia desde **Docentes → Editar / clave**.
2. **Inicio** → *Nueva sección* (código, asignatura, docente).
3. Abrir la sección → **Cargar matrícula** (ver `ejemplos/matricula_ejemplo.csv`; columnas `nombres, apellidos, cedula`).
4. El docente entra, abre su sección → **Iniciar y proyectar QR**.
5. Los alumnos escanean, ponen su cédula y el contador sube en vivo. Quien no tenga teléfono se marca con **Pasar lista manual**.
6. **Cerrar clase**. Las estadísticas y reportes se actualizan solos.
