# Arquitectura y decisiones de diseño

Este documento explica **qué** elegimos y **por qué**, para que cualquier integrante del equipo pueda entender y defender el proyecto. La regla general fue: *lo más simple que funcione bien*.

## 1. Vista general

```
 Teléfono del alumno          Laptop del docente (proyector)       Coordinador
        │                              │                               │
        └──────────────┬───────────────┴───────────────┬───────────────┘
                       ▼                               ▼
              ┌─────────────────────────────────────────────────┐
              │      Contenedor Docker (un solo proceso)        │
              │  ┌───────────────┐      ┌────────────────────┐  │
              │  │ React (build) │      │  FastAPI  /api/... │  │
              │  │ archivos .js  │      │  routers → services│  │
              │  └───────────────┘      └─────────┬──────────┘  │
              │                                   ▼             │
              │                         SQLite (asistencia.db)  │
              └─────────────────────────────────────────────────┘
```

Es un **monolito**: un repositorio, una imagen Docker, un proceso. FastAPI sirve tanto la API (`/api/...`) como el frontend compilado (cualquier otra ruta). No hay CORS que configurar, ni dos servidores que desplegar.

## 2. Decisiones de tecnología

| Decisión | Elegido | Alternativa descartada | Motivo |
|---|---|---|---|
| Framework backend | **FastAPI** | Flask | Valida el JSON automáticamente con Pydantic (menos código de validación), genera documentación interactiva en `/docs` (muy útil para la presentación y para que el equipo pruebe la API) y usa *type hints*, que hacen el código más legible. Para una API JSON + SPA es la opción más directa. |
| Frontend | **React + Vite** | Next.js | Next.js necesita su propio servidor Node (SSR) y rompería el monolito. Vite solo compila React a archivos estáticos que FastAPI sirve. Mismo React, mucho menos peso. |
| Base de datos | **SQLite** | PostgreSQL | Un archivo, cero configuración, cero contenedores extra. Soporta sin problema el volumen de una universidad (cientos de escrituras por minuto). Gracias al ORM, migrar a PostgreSQL es cambiar `DATABASE_URL`. |
| ORM | **SQLAlchemy 2.0** | SQL a mano | Clases Python ↔ tablas (POO), protección contra inyección SQL, independencia del motor. |
| Autenticación | **JWT + PBKDF2** (librería estándar) | sesiones en servidor, bcrypt | JWT no requiere guardar sesiones. PBKDF2 viene con Python (sin dependencias nativas) y es recomendado por OWASP. |
| Alumnos | **Sin cuenta**, solo cédula | Login por alumno | Lo pidió la especificación y reduce fricción en el aula: escanear → cédula → listo. |
| QR | Se genera **en el navegador** (`qrcode.react`) | Generar PNG en el servidor | El servidor solo entrega un código corto; el navegador dibuja el QR. Menos tráfico y menos código. |
| Gráficos | **Recharts** | Chart.js, D3 | Componentes React declarativos; un gráfico de barras en ~15 líneas. |
| Reportes | **openpyxl** (Excel) + **fpdf2** (PDF) | ReportLab, pandas | Ambas son puras Python y pequeñas. pandas sería sobredimensionado. |
| Dependencias Python | **uv** | pip + requirements.txt | Un solo comando (`uv sync`) crea el `.venv` e instala versiones exactas (`uv.lock`), tanto en local como en Docker. |
| Despliegue | **Docker multi-etapa + compose** | Instalar a mano en el VPS | `docker compose up -d --build` y listo. La BD vive en un volumen. |

### Lo que NO hicimos a propósito (evitar overengineering)
- Sin microservicios, colas, Redis ni WebSockets: el proyector consulta la API cada 2 s (*polling*), que para un aula es trivial.
- Sin Alembic (migraciones): `create_all` crea las tablas. Si el esquema cambia en producción, se añadiría Alembic en ese momento.
- Sin librería de estado global (Redux, etc.): un `Context` para el usuario y `useState` local alcanzan.
- Sin framework CSS: un único `styles.css`.

## 3. Modelo de datos

```
Usuario(id, usuario, nombre, clave_hash, rol: coordinador|docente)
Seccion(id, codigo UNIQUE, asignatura, coordinador_id → Usuario, docente_id → Usuario)
Estudiante(id, cedula UNIQUE, nombres, apellidos)
Inscripcion(id, seccion_id → Seccion, estudiante_id → Estudiante)  UNIQUE(seccion, estudiante)
Clase(id, seccion_id → Seccion, fecha, tema, abierta, secreto)
Asistencia(id, clase_id → Clase, estudiante_id → Estudiante, marcada_en)  UNIQUE(clase, estudiante)
```

- **Sección** es el centro del dominio. Su `codigo` lo define el coordinador y es único.
- Un **estudiante** se identifica por cédula y puede estar en varias secciones (relación N:M a través de **Inscripcion**, que es "la matrícula").
- Una **Clase** es cada encuentro en que se proyecta un QR (la llamamos así para no confundirla con la "sesión" de base de datos).
- Las restricciones `UNIQUE` hacen que la **base de datos** garantice que nadie se inscribe dos veces ni marca dos veces la misma clase, aunque lleguen dos peticiones simultáneas.

## 4. Organización del backend (POO y capas)

```
routers/   ← HTTP: recibe la petición, valida permisos, llama a services, responde.
services/  ← Lógica de negocio pura. No sabe nada de HTTP; se prueba fácil.
models.py  ← Entidades (clases ORM).
schemas.py ← Forma del JSON (clases Pydantic).
```

Clases principales:

| Clase | Archivo | Responsabilidad |
|---|---|---|
| `GeneradorCodigoQR` | `services/codigo_qr.py` | Generar y verificar el código rotativo. |
| `LectorMatricula` | `services/matricula.py` | Leer CSV/XLSX y devolver filas limpias + errores. |
| `CalculadoraEstadisticas` | `services/estadisticas.py` | Porcentajes por estudiante, por clase, por sección y generales. |
| `GeneradorReporte` (abstracta) → `GeneradorExcel`, `GeneradorPDF` | `services/reportes.py` | **Herencia y polimorfismo**: la ruta pide `GENERADORES[formato].generar(...)` sin saber qué formato es. Añadir CSV sería una subclase más. |
| Modelos ORM (`Seccion`, `Clase`…) | `models.py` | Encapsulan datos y propiedades derivadas (`Estudiante.nombre_completo`, `Seccion.estudiantes`). |

Los resultados de estadísticas son `@dataclass` (`ResumenSeccion`, `EstadisticaEstudiante`…), que FastAPI convierte a JSON directamente.

## 5. Algoritmos y estructuras de datos

### 5.1 Código QR rotativo (anti-foto)
Si el QR fuera fijo, un alumno podría fotografiarlo y enviarlo a quien no asistió. Usamos la misma idea que **TOTP** (Google Authenticator):

```
ventana = floor(ahora / 30 s)
código  = primeros 8 hex de HMAC-SHA256(secreto_de_la_clase, "clase_id:ventana")
```

- El QR codifica `https://dominio/asistir/<clase_id>?c=<código>`.
- El proyector pide el código vigente cada 2 s; al cambiar la ventana, el QR cambia solo.
- El servidor **no almacena** códigos: los recalcula. Acepta la ventana actual y la anterior (entre 30 y 60 s de validez) para no castigar a quien escaneó en el borde.
- Comparación con `hmac.compare_digest` (tiempo constante).
- Complejidad: **O(1)**.

**Limitación conocida:** alguien dentro del aula podría escanear y enviar el enlace en ese mismo minuto, o marcar con la cédula de otro. Mitigarlo del todo requeriría cuentas para alumnos o geolocalización, lo cual consideramos fuera del alcance del MVP. El docente puede corregir con la lista manual.

### 5.2 Validación del marcaje (`POST /api/publico/asistencia`)
Cadena de verificaciones que se detiene en el primer fallo:
1. La clase existe y está abierta.
2. El código es válido (5.1).
3. La cédula (normalizada: solo dígitos, `V-12.345.678` → `12345678`) pertenece a un estudiante **inscrito en esa sección** — una consulta con `JOIN`, usando índices únicos.
4. Se inserta la asistencia; si viola `UNIQUE(clase, estudiante)` se responde "ya tenías la asistencia registrada" (idempotente).

### 5.3 Carga de matrícula
- Se leen las filas del CSV (detecta `,` `;` o tabulador y codificación UTF-8/Latin-1) o del Excel.
- Encabezados normalizados (minúsculas, sin acentos) → se aceptan en cualquier orden.
- **Diccionario `cédula → fila`**: elimina duplicados dentro del archivo en O(1) por fila.
- Una sola consulta trae los estudiantes que ya existen (`WHERE cedula IN (...)`) a otro **diccionario**, y un **conjunto** con las cédulas ya inscritas en la sección. Así cada fila se procesa en O(1) y se evita el problema N+1 (una consulta por fila).
- Complejidad total: **O(n)** con n = filas.

### 5.4 Estadísticas de asistencia
Con E estudiantes, C clases y A asistencias de una sección:
1. Una consulta trae todos los pares `(clase_id, estudiante_id)`.
2. Un solo recorrido llena dos `Counter` (tablas hash): asistencias por estudiante y presentes por clase.
3. Fórmulas:
   - % estudiante = asistencias / C × 100
   - % clase = presentes / E × 100
   - % sección = A / (E × C) × 100
   - **En riesgo** si % estudiante < 75 % (mínimo habitual de los reglamentos).
4. Panel general del coordinador: promedio **ponderado** por cupos (Σ asistencias / Σ E×C), para que una sección de 5 alumnos no pese igual que una de 40.

Complejidad: **O(A + E + C)** — lineal.

### 5.5 Otras estructuras
- `set` de estudiantes presentes para pintar la lista manual (pertenencia O(1)).
- Ordenamiento por `(apellidos, nombres)` con `sorted` (Timsort, O(n log n)).

## 6. Seguridad y permisos

| Rol | Puede |
|---|---|
| Coordinador | Crear/editar/eliminar **sus** secciones, registrar docentes, cargar/retirar estudiantes, ver estadísticas generales y de cada sección, exportar reportes, abrir clases. |
| Docente | Ver **solo las secciones que dicta**, abrir/cerrar clases, proyectar QR, pasar lista manual, ver estadísticas y exportar reportes. |
| Alumno (anónimo) | Ver el nombre de la clase y marcar asistencia con su cédula, solo con un código vigente. |

- Si un usuario pide una sección ajena, la API responde **404** (no revela que existe).
- Contraseñas con PBKDF2-SHA256, 200 000 iteraciones y sal aleatoria.
- `SECRET_KEY` firma los JWT; **debe** cambiarse en producción (`.env`).

## 7. API (resumen)

La documentación completa e interactiva está en `/docs` con el servidor corriendo.

| Método | Ruta | Quién |
|---|---|---|
| POST | `/api/auth/login` | todos |
| GET/POST | `/api/docentes` | coordinador |
| GET/POST | `/api/secciones` | GET ambos (filtrado por rol), POST coordinador |
| PUT/DELETE | `/api/secciones/{id}` | coordinador |
| POST | `/api/secciones/{id}/matricula` | coordinador |
| GET | `/api/secciones/{id}/estadisticas` | ambos |
| GET | `/api/secciones/{id}/reporte?formato=pdf\|excel` | ambos |
| GET | `/api/estadisticas/general` | coordinador |
| GET/POST | `/api/secciones/{id}/clases` | ambos |
| GET | `/api/clases/{id}/qr` | ambos |
| POST | `/api/clases/{id}/cerrar` · `/reabrir` | ambos |
| GET/PUT | `/api/clases/{id}/asistentes[/{estudiante}]` | ambos |
| GET | `/api/publico/clases/{id}?c=código` | público |
| POST | `/api/publico/asistencia` | público |

## 8. Pruebas

`backend/tests/` contiene:
- `test_servicios.py`: pruebas unitarias del algoritmo del QR y del lector de matrícula.
- `test_flujo.py`: recorrido completo por la API (crear docente y sección → cargar matrícula → abrir clase → alumnos marcan → estadísticas → PDF/Excel), con base de datos temporal.

```bash
cd backend && uv run pytest
```
