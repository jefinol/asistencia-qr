# Guía magistral del backend de **Asistencia QR**

> **Para quién es esta guía:** para compañeros que saben Python básico (variables, `input()`, `print()`, `if`, `match`, funciones, recursividad, listas y diccionarios) y están empezando con POO. No asume que sepas qué es un servidor, una API, una base de datos ni Docker.
>
> **Cómo leerla:** va de lo sencillo a lo complejo. Las Partes 1–3 son conceptos (sin código del proyecto). La Parte 4 recorre el código archivo por archivo. Las Partes 5–6 son "diccionarios" de sintaxis y librerías para consultar. Las Partes 7–8 cubren pruebas y Docker. Al final hay un recorrido completo de una petición, preguntas típicas de la profesora con sus respuestas, un glosario y ejercicios.
>
> El frontend (React) **no** se explica aquí; solo se menciona cuando hace falta para entender al backend.

---

## Índice

- [Parte 1 — El producto: qué es, qué problema resuelve y por qué vale](#parte-1--el-producto)
- [Parte 2 — Fundamentos: de un programa de consola a un backend](#parte-2--fundamentos-de-un-programa-de-consola-a-un-backend)
- [Parte 3 — El entorno de desarrollo: Python, venv, uv, variables de entorno](#parte-3--el-entorno-de-desarrollo)
- [Parte 4 — Recorrido por el código, archivo por archivo](#parte-4--recorrido-por-el-código)
- [Parte 5 — Diccionario de sintaxis &#34;nueva y rara&#34;](#parte-5--diccionario-de-sintaxis-nueva-y-rara)
- [Parte 6 — Todas las librerías y módulos usados](#parte-6--todas-las-librerías-y-módulos)
- [Parte 7 — Pruebas (tests) y unit testing](#parte-7--pruebas-tests)
- [Parte 8 — Docker y despliegue](#parte-8--docker-y-despliegue)
- [Parte 9 — Una petición de principio a fin](#parte-9--una-petición-de-principio-a-fin)
- [Parte 10 — Prácticas profesionales y limitaciones honestas](#parte-10--prácticas-profesionales-y-limitaciones-honestas)
- [Parte 11 — Preguntas que puede hacer la profesora](#parte-11--preguntas-que-puede-hacer-la-profesora)
- [Glosario](#glosario)
- [Ejercicios para el equipo](#ejercicios-para-el-equipo)

---

# Parte 1 — El producto

## 1.1 El problema

Piensen en cómo se pasa lista hoy en la mayoría de las aulas:

1. **Lista en papel que circula.** Tarda, se pierde, y cualquiera firma por un amigo que no vino.
2. **El profesor nombra uno por uno.** Con 40 alumnos se van 5–10 minutos de cada clase. En un semestre de 30 clases son entre 2,5 y 5 horas perdidas por sección.
3. **Los datos quedan muertos.** Aunque la lista exista, nadie la pasa a una hoja de cálculo. Cuando el reglamento dice "quien tenga menos del 75 % de asistencia no puede presentar", el profesor tiene que contar a mano, al final, cuando ya es tarde para avisarle al estudiante.
4. **La coordinación no ve nada.** El coordinador académico no sabe qué secciones tienen problemas de asistencia hasta que alguien se queja.

## 1.2 La solución: Asistencia QR

Un sistema web donde:

| Actor                 | Qué hace                                                                                                                                                                                                                                                                                                          |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Coordinador** | Crea las secciones (código + asignatura + docente), registra a los docentes, carga la matrícula con un archivo CSV o Excel (`nombres, apellidos, cedula`), y ve un panel con las estadísticas de **todas** sus secciones.                                                                               |
| **Docente**     | Abre la sección, pulsa "Iniciar clase" y proyecta un **código QR que cambia cada 30 segundos**. Ve en vivo cuántos alumnos han marcado. Al final cierra la clase. Ve estadísticas de su sección y descarga reportes en **PDF** o **Excel**. Puede marcar a mano a quien no tenga teléfono. |
| **Alumno**      | Escanea el QR con la cámara del teléfono, se abre una página, escribe su cédula y listo. **No necesita cuenta, contraseña ni instalar nada.**                                                                                                                                                           |

### Un día de clase, contado como historia

1. 7:00 a. m. El profesor Ramírez entra a la app en la laptop conectada al proyector y pulsa **Iniciar y proyectar QR**.
2. En la pared aparece un QR grande y un contador: *"0 de 38 presentes"*.
3. Ana saca el teléfono, apunta la cámara, se abre `https://asistencia.../asistir/15?c=a3f91c07`. Ve "Programación III – Sección PROG3-A". Escribe `V-28.123.456` y pulsa Marcar. Le sale *"¡Asistencia registrada, Pérez Rodríguez, Ana María!"*.
4. El contador del proyector sube a *"1 de 38"* (la pantalla consulta al servidor cada 2 segundos).
5. Luis le toma foto al QR y se la manda a Pedro, que está en su casa. Cuando Pedro abre la foto 3 minutos después, el código ya **expiró** (cambia cada 30 s y solo se acepta el actual o el anterior). Pedro no puede marcar.
6. José no tiene batería. El profesor abre **Pasar lista manual** y lo marca con un clic.
7. Al terminar, el profesor pulsa **Cerrar clase**. A partir de ese momento nadie más puede marcar.
8. Las estadísticas ya están actualizadas: porcentaje por alumno, por clase y de la sección, con los alumnos **en riesgo** (por debajo de 75 %) resaltados en rojo. El reporte PDF/Excel se descarga con un clic.

## 1.3 Propuesta de valor

> **"Pasar lista en 1 minuto, sin papel, sin trampas fáciles y con estadísticas al instante."**

- **Ahorra tiempo de clase**: 40 alumnos marcan en paralelo, cada uno desde su teléfono.
- **Dificulta el fraude**: el QR rotativo hace inútil la foto reenviada por WhatsApp.
- **Cero fricción para el alumno**: no hay cuentas ni apps. Escanear + cédula.
- **Datos vivos**: el docente sabe *hoy* quién está en riesgo, no al final del semestre.
- **Visión institucional**: el coordinador compara secciones con un promedio ponderado.
- **Barato de operar**: un solo contenedor Docker en un VPS de pocos dólares; la base de datos es un archivo.

## 1.4 Qué NO hace (alcance del MVP)

Un **MVP** (*Minimum Viable Product*, producto mínimo viable) es la versión más pequeña que ya resuelve el problema de verdad. Decidimos a propósito **no** hacer:

- Cuentas para alumnos ni geolocalización (ver limitaciones en la Parte 10).
- Varios coordinadores: hay **uno**, creado al arrancar. En la vida real lo daría de alta un superusuario (Control de Estudios).
- Notificaciones por correo, app móvil nativa, microservicios, WebSockets, Redis.

Decir "esto no lo hicimos y por qué" es una señal de dominio, no de debilidad.

---

# Parte 2 — Fundamentos: de un programa de consola a un backend

## 2.1 Lo que ya saben hacer

Miren el ejercicio `recursiva_compra.py` que hicimos en el Corte II:

```python
nombre = input("Ingrese el nombre del artículo (o escribe 'fin' para terminar): ").strip()
precio = float(input(f"Ingrese el precio de '{nombre}': $"))
lista_articulos.append({"nombre": nombre, "precio": precio})
```

Ese programa tiene cuatro características:

1. **Un solo usuario**: la persona sentada frente a la consola.
2. **Entrada por `input()`**, salida por `print()`.
3. **Memoria volátil**: la lista `lista_articulos` desaparece cuando el programa termina.
4. **Corre y muere**: empieza, hace su trabajo y se cierra.

Y en `match.py` tenían un menú:

```python
match opcion:
    case 1: ...  # consultar saldo
    case 2: ...  # depositar
    case 3: ...  # retirar
```

## 2.2 Lo que hace un backend

Un **backend** (o *servidor*) es un programa que hace exactamente lo contrario en cada punto:

| Programa de consola (lo que conocen)                                                      | Backend (este proyecto)                                                                                                |
| ----------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Un usuario                                                                                | Cientos de usuarios a la vez, desde teléfonos y laptops                                                               |
| Entrada: `input()`                                                                      | Entrada: una **petición HTTP** que llega por la red                                                             |
| Salida: `print()`                                                                       | Salida: una **respuesta HTTP**, normalmente en formato **JSON**                                            |
| Memoria: variables y listas que se pierden                                                | Memoria: una **base de datos** en disco que sobrevive a reinicios                                                |
| Corre y muere                                                                             | **Nunca termina**: se queda esperando peticiones para siempre                                                    |
| Menú con `match opcion:`                                                               | **Rutas**: según la URL y el método, se ejecuta una función distinta                                          |
| Si el usuario escribe "abc" en `float(input())`, el programa explota con `ValueError` | Los datos se **validan** antes de usarlos; si son inválidos se responde un error claro y el servidor sigue vivo |

El menú `match` es la mejor analogía: en el backend, el "número de opción" es la combinación **método + ruta**. Por ejemplo:

```text
POST /api/auth/login              → función login()
GET  /api/secciones               → función listar()
POST /api/publico/asistencia      → función marcar()
```

FastAPI es, en esencia, un `match` gigante y automático que mira cada petición que llega y llama a la función correcta.

## 2.3 Cliente y servidor

```text
┌────────────┐   1. petición (request)   ┌────────────┐
│  CLIENTE   │ ────────────────────────► │  SERVIDOR  │
│ (navegador,│                           │ (nuestro   │
│  teléfono) │ ◄──────────────────────── │  backend)  │
└────────────┘   2. respuesta (response) └────────────┘
```

- El **cliente** pide. En nuestro caso: el navegador del docente, el teléfono del alumno, o un test automático.
- El **servidor** responde. Nunca toma la iniciativa: solo contesta lo que le piden.

**Analogía del restaurante:** el cliente (comensal) no entra a la cocina; le pide al mesonero (la API) algo del menú (las rutas). La cocina (la lógica y la base de datos) prepara el plato y el mesonero lo trae. El comensal no necesita saber cómo se cocina, y la cocina no deja que el comensal toque las ollas.

## 2.4 HTTP: el idioma de la web

**HTTP** (*HyperText Transfer Protocol*) es el conjunto de reglas con el que cliente y servidor se hablan. Una petición HTTP tiene cuatro partes:

```http
POST /api/publico/asistencia HTTP/1.1          ← 1. MÉTODO + 2. RUTA
Host: asistencia.midominio.com
Content-Type: application/json                 ← 3. CABECERAS (headers): metadatos
Authorization: Bearer eyJhbGciOi...

{"clase_id": 15, "codigo": "a3f91c07", "cedula": "V-28.123.456"}   ← 4. CUERPO (body)
```

Y la respuesta:

```http
HTTP/1.1 200 OK                                ← CÓDIGO DE ESTADO
Content-Type: application/json

{"mensaje": "¡Asistencia registrada!", "estudiante": "Pérez Rodríguez, Ana María"}
```

### Los métodos (verbos) que usamos

| Método    | Significado                                       | Ejemplo en el proyecto                             |
| ---------- | ------------------------------------------------- | -------------------------------------------------- |
| `GET`    | **Leer**. No cambia nada.                   | `GET /api/secciones` → lista mis secciones      |
| `POST`   | **Crear** algo nuevo o ejecutar una acción | `POST /api/secciones` → crea una sección       |
| `PUT`    | **Reemplazar/actualizar** algo existente    | `PUT /api/secciones/3` → edita la sección 3    |
| `DELETE` | **Borrar**                                  | `DELETE /api/secciones/3` → borra la sección 3 |

### Los códigos de estado que usamos

Son números de tres dígitos. El primer dígito dice la familia: **2xx = éxito**, **4xx = el cliente se equivocó**, **5xx = el servidor falló**.

| Código       | Nombre               | Cuándo lo devolvemos                                                                                      |
| ------------- | -------------------- | ---------------------------------------------------------------------------------------------------------- |
| **200** | OK                   | Todo bien, aquí están los datos                                                                          |
| **201** | Created              | Se creó algo (docente, sección, clase)                                                                   |
| **204** | No Content           | Se hizo (p. ej. se borró) y no hay nada que devolver                                                      |
| **400** | Bad Request          | Petición con sentido pero inválida: "la clase está cerrada", "el QR expiró", "clave actual incorrecta" |
| **401** | Unauthorized         | **No sé quién eres**: no mandaste token, o está vencido, o la clave es incorrecta                 |
| **403** | Forbidden            | **Sé quién eres, pero no tienes permiso**: un docente intentando ver el panel del coordinador      |
| **404** | Not Found            | No existe… **o no te lo voy a mostrar** (ver Parte 4, seguridad)                                    |
| **409** | Conflict             | Choca con algo existente: código de sección o usuario repetido                                           |
| **422** | Unprocessable Entity | El JSON no cumple el formato (lo genera FastAPI automáticamente, ver Pydantic)                            |

> **Truco para la exposición:** 401 = "¿quién eres?"; 403 = "ya sé quién eres y no puedes".

## 2.5 JSON: el formato de los datos

**JSON** (*JavaScript Object Notation*) es texto que se parece muchísimo a los diccionarios y listas de Python:

```json
{
  "id": 3,
  "codigo": "PROG3-A",
  "asignatura": "Programación III",
  "docente": {"id": 2, "usuario": "prof", "nombre": "Prof. Ramírez", "rol": "docente"}
}
```

| JSON                 | Python               |
| -------------------- | -------------------- |
| `{ }` objeto       | `dict`             |
| `[ ]` arreglo      | `list`             |
| `"texto"`          | `str`              |
| `3`, `3.5`       | `int`, `float`   |
| `true` / `false` | `True` / `False` |
| `null`             | `None`             |

¿Por qué texto? Porque cualquier lenguaje lo puede leer: el backend está en Python y el frontend en JavaScript, y se entienden gracias a JSON.

## 2.6 ¿Qué es una API?

**API** (*Application Programming Interface*) es un **contrato**: "si me mandas *esto*, a *esta dirección*, te respondo *aquello*". Es el menú del restaurante: dice qué puedes pedir y qué te van a traer, sin decirte cómo se cocina.

Nuestra API es el conjunto de todas las rutas `/api/...`. La lista completa está en `docs/ARQUITECTURA.md` §7, y con el servidor encendido se ve **interactiva** en `http://localhost:8000/docs`.

## 2.7 ¿Qué es REST?

**REST** (*REpresentational State Transfer*) no es una librería: es un **estilo** de diseñar APIs, con unas reglas:

1. **Todo es un recurso con una URL.** Las secciones viven en `/api/secciones`, la sección 3 en `/api/secciones/3`, las clases de la sección 3 en `/api/secciones/3/clases`. Los nombres son **sustantivos en plural**, no verbos (`/secciones`, no `/crearSeccion`).
2. **El método HTTP dice la acción.** La misma URL `/api/secciones/3` se lee con `GET`, se edita con `PUT` y se borra con `DELETE`.
3. **Sin estado (*stateless*).** El servidor no "recuerda" al cliente entre una petición y otra. Cada petición trae todo lo necesario, incluido **quién eres** (el token JWT en la cabecera `Authorization`). Por eso podemos reiniciar el servidor sin que nadie pierda su sesión.
4. **Representaciones.** El servidor no te da "la sección" (que es una fila en una tabla), te da una *representación* de ella en JSON.
5. **Códigos de estado con significado** (los de la tabla anterior).

### CRUD ↔ HTTP ↔ SQL

**CRUD** son las cuatro operaciones básicas sobre datos. En nuestro proyecto, para las secciones:

| CRUD             | HTTP       | Ruta                                         | SQL que termina ejecutándose     |
| ---------------- | ---------- | -------------------------------------------- | --------------------------------- |
| **C**reate | `POST`   | `/api/secciones`                           | `INSERT INTO secciones ...`     |
| **R**ead   | `GET`    | `/api/secciones` y `/api/secciones/{id}` | `SELECT ... FROM secciones ...` |
| **U**pdate | `PUT`    | `/api/secciones/{id}`                      | `UPDATE secciones SET ...`      |
| **D**elete | `DELETE` | `/api/secciones/{id}`                      | `DELETE FROM secciones ...`     |

### Somos REST "pragmático"

Algunas rutas son **acciones**, no recursos puros: `POST /api/clases/{id}/cerrar`, `POST /api/clases/{id}/reabrir`. Un purista diría `PATCH /api/clases/{id}` con `{"abierta": false}`. Elegimos la versión con verbo porque se lee mejor y es lo que hacen muchas APIs reales (GitHub, Stripe). También `PUT /api/clases/{id}/asistentes/{est}` **alterna** (marca/desmarca), lo que técnicamente rompe la regla de que `PUT` sea *idempotente* (repetirlo debería dar el mismo resultado). Saberlo y justificarlo es mejor que no saberlo.

> **Idempotente**: hacer la operación una vez o diez veces deja el mismo resultado. `GET`, `PUT` y `DELETE` deberían serlo; `POST` no. Nuestro `POST /api/publico/asistencia` sí se comporta de forma idempotente: si marcas dos veces, la segunda responde "Ya tenías la asistencia registrada" y no duplica nada.

## 2.8 La arquitectura: ¿es MVC?

**Respuesta corta:** *casi*. Es una **arquitectura en capas** inspirada en MVC, que es lo habitual en las APIs modernas. Vamos por partes.

### Qué es MVC

**MVC** (*Model–View–Controller*) divide una aplicación en tres responsabilidades:

- **Model (Modelo):** los datos y sus reglas. "Qué es una sección".
- **View (Vista):** lo que ve el usuario. "La pantalla con la tabla de secciones".
- **Controller (Controlador):** recibe la acción del usuario, usa el modelo y elige la vista. "Cuando pulsan Guardar, valido, guardo y muestro la lista".

En un MVC clásico (Django con plantillas, Laravel, Ruby on Rails), el servidor genera el HTML de la vista.

### Qué hacemos nosotros

Nuestro backend **no genera pantallas**: devuelve JSON, y la pantalla la dibuja React en el navegador. Por eso la "V" se va al frontend, y en el backend usamos estas capas:

```text
                 ┌──────────────────────────────────────────┐
  Petición HTTP  │  routers/        ← CONTROLADORES          │
 ──────────────► │  auth.py, secciones.py, clases.py         │
                 │  · reciben la petición                    │
                 │  · validan permisos (Depends)             │
                 │  · llaman a services                      │
                 │  · devuelven la respuesta                 │
                 └───────────────┬──────────────────────────┘
                                 │ usa
                 ┌───────────────▼──────────────────────────┐
                 │  services/       ← LÓGICA DE NEGOCIO      │
                 │  codigo_qr, matricula, estadisticas,      │
                 │  reportes. No saben nada de HTTP.         │
                 └───────────────┬──────────────────────────┘
                                 │ usa
                 ┌───────────────▼──────────────────────────┐
                 │  models.py       ← MODELOS (tablas ORM)   │
                 │  database.py     ← conexión               │
                 └───────────────┬──────────────────────────┘
                                 ▼
                          SQLite (archivo .db)

  schemas.py   ← "forma" del JSON de entrada y salida (la "vista" en formato datos)
  security.py  ← contraseñas, tokens y roles (transversal: lo usan los routers)
  config.py    ← configuración (transversal)
```

| MVC clásico | Nuestro proyecto                                                                                                      |
| ------------ | --------------------------------------------------------------------------------------------------------------------- |
| Model        | `models.py` (datos) + `services/` (reglas de negocio)                                                             |
| View         | El **frontend React**. En el backend, la "representación" la definen los `schemas.py` (qué JSON se muestra) |
| Controller   | `routers/`                                                                                                          |

Algunos libros lo llaman **"arquitectura en capas"** (*layered*), otros **"MVC + capa de servicios"**, o simplemente **routers–services–models**. Cualquiera de los tres nombres es defendible; lo importante es la idea:

> **Cada capa tiene una sola responsabilidad y solo habla con la de abajo.**

¿Por qué importa? Porque:

- La lógica del QR (`services/codigo_qr.py`) se puede **probar** sin servidor ni base de datos (lo hacemos en `test_servicios.py`).
- Si mañana cambiamos FastAPI por Flask, los `services` no se tocan.
- Si cambiamos SQLite por PostgreSQL, ni los routers ni los services se tocan.
- Cada archivo es corto y se entiende solo.

## 2.9 Monolito vs. microservicios

- **Monolito:** una sola aplicación, un repositorio, un proceso. Es lo que hicimos.
- **Microservicios:** muchas aplicaciones pequeñas que se hablan por red (una para usuarios, otra para QR, otra para reportes…).

Los microservicios sirven cuando tienes cientos de programadores y millones de usuarios. Para un equipo de estudiantes y una universidad, un monolito es **más simple, más rápido y más fácil de desplegar**. Nuestro monolito sirve **la API y el frontend compilado desde el mismo proceso**: no hay dos servidores ni problemas de CORS (ver Glosario).

---

# Parte 3 — El entorno de desarrollo

## 3.1 El problema que resolvemos

Imaginen que el proyecto necesita FastAPI versión 0.162 y otro proyecto de su computadora necesita FastAPI 0.95. Si instalan todo "en el Python del sistema" con `pip install`, uno de los dos se rompe. Además, cuando un compañero clone el repositorio, ¿cómo sabe qué instalar y en qué versión?

## 3.2 Entorno virtual (`venv`)

Un **entorno virtual** es una **carpeta** (en nuestro caso `backend/.venv/`) con una copia aislada de Python y sus propias librerías. Cada proyecto tiene la suya, así que no se pisan.

```text
backend/
├── .venv/                ← entorno virtual (NO se sube a git: está en .gitignore)
│   ├── Scripts/python.exe   (Windows)  o  bin/python (Linux/Mac)
│   └── Lib/site-packages/   ← aquí viven fastapi, sqlalchemy, etc.
├── app/
└── pyproject.toml
```

A la manera clásica se haría así:

```bash
python -m venv .venv
```

```bash
.venv\Scripts\activate
```

```bash
pip install fastapi sqlalchemy ...
```

Nosotros **no** hacemos eso a mano: lo hace `uv`.

## 3.3 `uv`: el gestor de proyectos

**uv** (de la empresa Astral, escrito en Rust) reemplaza a `pip`, `venv`, `pip-tools` y `pyenv` con un solo programa, y es entre 10 y 100 veces más rápido que `pip`.

| Comando                    | Qué hace                                                                                                                                                           |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `uv sync`                | Lee `pyproject.toml` y `uv.lock`, **crea `.venv` si no existe** e instala exactamente las versiones bloqueadas. Un compañero nuevo solo necesita esto. |
| `uv run <comando>`       | Ejecuta el comando **dentro** del `.venv`, sin tener que "activarlo". Ej.: `uv run pytest`, `uv run uvicorn app.main:app --reload`.                     |
| `uv add <paquete>`       | Añade una dependencia a `pyproject.toml`, actualiza `uv.lock` e instala.                                                                                       |
| `uv add --dev <paquete>` | Igual, pero como dependencia **solo de desarrollo** (pytest, httpx).                                                                                          |

Además `uv` lee `backend/.python-version` (que dice `3.12`) y, si no tienes Python 3.12, **lo descarga solo**.

## 3.4 `pyproject.toml`, línea por línea

Es el archivo estándar de Python (PEP 621) que describe el proyecto. Formato **TOML** (parecido a un `.ini`):

```toml
[project]
name = "asistencia-qr"
version = "0.1.0"
description = "Sistema de control de asistencia por QR (Programación III)"
readme = "../README.md"
requires-python = ">=3.12"          # necesitamos 3.12+ (usamos sintaxis como  int | None  y  match)
dependencies = [                    # lo que la app necesita PARA FUNCIONAR
    "fastapi>=0.115",               # ">=" : esta versión o una más nueva
    "uvicorn[standard]>=0.30",      # [standard] = "extras": instala también paquetes opcionales que aceleran uvicorn
    "sqlalchemy>=2.0",
    "pyjwt>=2.9",
    "python-multipart>=0.0.9",
    "openpyxl>=3.1",
    "fpdf2>=2.7",
    "tzdata",                       # sin versión mínima
]

[dependency-groups]
dev = [                             # lo que SOLO necesitamos al desarrollar (no va a producción)
    "pytest>=8",
    "httpx>=0.27",
]

[tool.pytest.ini_options]           # configuración de pytest
testpaths = ["tests"]               # busca pruebas en la carpeta tests/
pythonpath = ["."]                  # añade backend/ al path para que "import app" funcione
```

## 3.5 `uv.lock`: el candado

`pyproject.toml` dice "FastAPI **0.115 o más nueva**". Pero si hoy un compañero instala y le toca la 0.162 y mañana otro instala y le toca la 0.170, podrían comportarse distinto. El archivo **`uv.lock`** congela la versión **exacta** de *todas* las librerías, incluidas las dependencias de las dependencias (FastAPI necesita Starlette y Pydantic; Pydantic necesita pydantic-core…). Hoy el lock fija, por ejemplo: `fastapi 0.162.2`, `sqlalchemy 2.1.8`, `pydantic 2.14.3`, `uvicorn 0.54.0`, `pytest 9.2.0`.

**Regla:** `uv.lock` **sí** se sube a git. Así todos (y Docker) instalan exactamente lo mismo. Esto se llama **builds reproducibles**.

## 3.6 Variables de entorno y `.env`

Hay datos que **no deben estar en el código**:

- **Secretos**: la clave que firma los tokens (`SECRET_KEY`), la clave del coordinador.
- **Cosas que cambian entre tu laptop y el servidor**: dónde está la base de datos, la zona horaria.

Las **variables de entorno** son pares `NOMBRE=valor` que el sistema operativo le pasa a un programa al arrancar. En Python se leen con `os.getenv("NOMBRE", "valor_por_defecto")`.

El archivo **`.env`** es una lista de esas variables que Docker Compose carga. El repositorio trae **`.env.example`** (plantilla sin secretos reales) y el `.env` verdadero **no se sube a git** (está en `.gitignore`):

```ini
SECRET_KEY=pon-aqui-una-clave-larga-y-aleatoria
ADMIN_USUARIO=coordinador
ADMIN_CLAVE=cambia-esta-clave
TOKEN_HORAS=12
QR_VENTANA_SEGUNDOS=30
ZONA_HORARIA=America/Caracas
```

> Esta práctica viene de **The Twelve-Factor App**, una guía muy citada de buenas prácticas: *"guarda la configuración en el entorno"*.

## 3.7 Los archivos "ocultos" del repositorio

| Archivo             | Para qué sirve                                                                                                                                                                                                                                                           |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `.gitignore`      | Lo que git **no** debe subir: `.venv/`, `__pycache__/`, `node_modules/`, la base de datos `backend/data/`, el `.env` con secretos.                                                                                                                        |
| `.gitattributes`  | `* text=auto eol=lf`: todos los archivos de texto se guardan con saltos de línea **LF** (estilo Linux). Windows usa **CRLF**; sin esto, un script creado en Windows puede fallar en el servidor Linux y git mostraría todas las líneas como "cambiadas". |
| `.dockerignore`   | Como `.gitignore` pero para Docker: no copiar a la imagen `node_modules`, `.venv`, los tests ni el `.env`.                                                                                                                                                        |
| `.python-version` | Le dice a `uv` qué versión de Python usar: `3.12`.                                                                                                                                                                                                                  |
| `.env.example`    | Plantilla de configuración para copiar a `.env`.                                                                                                                                                                                                                       |

## 3.8 Cómo arrancar en desarrollo

```bash
cd backend
```

```bash
uv sync
```

```bash
uv run uvicorn app.main:app --reload
```

- `uvicorn` es el **servidor** que escucha en el puerto 8000.
- `app.main:app` significa: "en el módulo `app/main.py`, usa la variable llamada `app`".
- `--reload`: cada vez que guardas un archivo, se reinicia solo (solo para desarrollo).

Abran `http://localhost:8000/docs` y verán **Swagger UI**: una página generada automáticamente donde se puede probar cada ruta con botones. Es la mejor herramienta para la exposición.

---

# Parte 4 — Recorrido por el código

Vamos en el **orden en que los archivos dependen unos de otros**: primero lo que no depende de nada (configuración) y al final lo que lo une todo (`main.py`).

```text
config.py ─► database.py ─► models.py ─► schemas.py
                                 │            │
                                 ▼            ▼
                            security.py ◄─────┘
                                 │
        services/ (codigo_qr, matricula, estadisticas, reportes)
                                 │
                    routers/ (auth, secciones, clases)
                                 │
                              main.py
```

## 4.1 `app/__init__.py` y los paquetes

Una carpeta con un archivo `__init__.py` es un **paquete**: Python la trata como un módulo que contiene otros módulos. Gracias a eso podemos escribir `from app.services.codigo_qr import GeneradorCodigoQR`. Nuestros `__init__.py` solo tienen un *docstring* (una cadena de documentación), y eso basta.

## 4.2 `config.py` — la configuración en un solo lugar

En `ventasbasica.py` hicieron esto:

```python
TASA_IMPUESTO = 0.16
DESCUENTO_FIJO = 5.0
```

`config.py` es la versión profesional de esa idea: **todas** las constantes configurables viven en un solo sitio, y además se pueden cambiar sin tocar el código, con variables de entorno.

```python
@dataclass(frozen=True)
class Settings:
    secret_key: str = os.getenv("SECRET_KEY", "cambiar-esta-clave-en-produccion")
    database_url: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'asistencia.db'}"
    )
    token_horas: int = int(os.getenv("TOKEN_HORAS", "12"))
    qr_ventana_segundos: int = int(os.getenv("QR_VENTANA_SEGUNDOS", "30"))
    ...

settings = Settings()
```

Qué hay que entender:

- **`@dataclass`** genera automáticamente el `__init__`, el `__repr__` y el `__eq__` de la clase a partir de los atributos anotados. Es una clase "de datos".
- **`frozen=True`** la vuelve **inmutable**: `settings.secret_key = "x"` lanzaría un error. La configuración no debe cambiar mientras el programa corre.
- **`os.getenv("SECRET_KEY", "valor")`** lee la variable de entorno; si no existe, usa el valor por defecto.
- **`int(os.getenv("TOKEN_HORAS", "12"))`**: las variables de entorno **siempre son texto**, por eso convertimos a `int` (igual que hacían con `int(input(...))`).
- **`settings = Settings()`** crea **una sola instancia** que todo el proyecto importa (`from .config import settings`). Es un patrón parecido al *Singleton*.
- **`BASE_DIR = Path(__file__).resolve().parent.parent`**: `__file__` es la ruta de este mismo archivo (`backend/app/config.py`); `.resolve()` la vuelve absoluta; `.parent` sube a `app/` y otro `.parent` sube a `backend/`.
- **`BASE_DIR / 'data' / 'asistencia.db'`**: con `pathlib`, el operador `/` **une rutas** (no divide). Funciona igual en Windows y Linux.

> **Detalle fino que conviene saber:** los valores por defecto de una dataclass se evalúan **una sola vez, cuando Python lee la clase**, es decir, al importar `config.py`. Por eso los tests (Parte 7) cambian las variables de entorno **antes** de importar la app.

### La función `hoy()` y la zona horaria

```python
def hoy() -> date:
    """Fecha actual en la zona horaria de la institución."""
    return datetime.now(ZoneInfo(settings.zona_horaria)).date()
```

Los servidores y Docker suelen estar en **UTC** (hora universal). Venezuela es UTC−4. Una clase a las 9:00 p. m. en Caracas ya es la 1:00 a. m. del **día siguiente** en UTC. Si usáramos `date.today()`, esa clase quedaría con la fecha equivocada. `hoy()` siempre calcula la fecha en `America/Caracas` (configurable con `ZONA_HORARIA`).

## 4.3 Bases de datos desde cero (antes de ver `database.py`)

### ¿Qué es una base de datos relacional?

Piensen en un libro de Excel:

- Cada **hoja** es una **tabla** (`estudiantes`, `secciones`…).
- Cada **columna** es un **campo** con un tipo (`cedula: texto`, `id: número`).
- Cada **fila** es un **registro** (un estudiante concreto).

```text
Tabla: estudiantes
┌────┬──────────┬──────────────┬──────────────────┐
│ id │ cedula   │ nombres      │ apellidos        │
├────┼──────────┼──────────────┼──────────────────┤
│ 1  │ 28123456 │ Ana María    │ Pérez Rodríguez  │
│ 2  │ 27987654 │ Luis Alberto │ Gómez            │
└────┴──────────┴──────────────┴──────────────────┘
```

Conceptos clave:

| Concepto                      | Significado                                                                                                                                    | En el proyecto                                                                                          |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Clave primaria (PK)** | Columna que identifica cada fila de forma única                                                                                               | `id` en todas las tablas                                                                              |
| **Clave foránea (FK)** | Columna que **apunta** al `id` de otra tabla                                                                                           | `secciones.docente_id → usuarios.id`                                                                 |
| **UNIQUE**              | Prohíbe valores repetidos                                                                                                                     | `estudiantes.cedula`, `secciones.codigo`, y el par `(clase_id, estudiante_id)` en `asistencias` |
| **Índice**             | Estructura (tipo árbol B) que acelera las búsquedas por esa columna, como el índice de un libro                                             | `index=True` en `cedula`, `codigo`, `usuario`                                                   |
| **Relación 1:N**       | "Uno a muchos": una sección tiene muchas clases                                                                                               | `Seccion` → `Clase`                                                                                |
| **Relación N:M**       | "Muchos a muchos": un estudiante está en muchas secciones y una sección tiene muchos estudiantes. Se resuelve con una **tabla puente** | `Inscripcion`                                                                                         |
| **SQL**                 | El lenguaje para consultar bases de datos relacionales                                                                                         | `SELECT * FROM estudiantes WHERE cedula = '28123456'`                                                 |
| **Transacción**        | Grupo de cambios que se aplican **todos o ninguno**                                                                                      | `db.commit()` / `db.rollback()`                                                                     |

### ¿Por qué no guardar todo en una lista como en `recursiva_compra.py`?

Porque esa lista vive en la memoria RAM y **se borra al cerrar el programa**. Una base de datos guarda en disco, permite buscar rápido con índices, garantiza reglas (no repetir cédulas) aunque lleguen dos peticiones al mismo tiempo, y deja que muchos usuarios lean y escriban a la vez.

### SQLite

Usamos **SQLite**: una base de datos completa que vive en **un solo archivo** (`asistencia.db`). No hay que instalar un servidor de base de datos. Python ya trae el módulo `sqlite3`. Para una universidad sobra, y si algún día hace falta **PostgreSQL**, basta con cambiar `DATABASE_URL` gracias al ORM.

### ¿Qué es un ORM?

**ORM** (*Object-Relational Mapping*, mapeo objeto-relacional) es una traducción automática entre **clases de Python** y **tablas SQL**:

| Mundo POO (Python)                            | Mundo relacional (SQL)                              |
| --------------------------------------------- | --------------------------------------------------- |
| Clase `Estudiante`                          | Tabla `estudiantes`                               |
| Atributo `cedula`                           | Columna `cedula`                                  |
| Objeto `Estudiante(cedula="111", ...)`      | Fila                                                |
| `estudiante.nombres = "Ana"` + `commit()` | `UPDATE estudiantes SET nombres='Ana' WHERE id=1` |
| `seccion.clases`                            | `SELECT * FROM clases WHERE seccion_id = ?`       |

Sin ORM escribiríamos SQL como texto, a mano. Con ORM escribimos Python, y ganamos:

1. **POO de verdad**: los datos son objetos con métodos y propiedades.
2. **Protección contra inyección SQL**: los valores siempre van como parámetros, nunca pegados al texto de la consulta.
3. **Independencia del motor**: el mismo código sirve para SQLite, PostgreSQL o MySQL.

Usamos **SQLAlchemy 2.0**, el ORM más usado en Python.

> **Inyección SQL**, explicada: si alguien escribe como cédula `' OR 1=1 --` y el programador hizo `f"SELECT * FROM estudiantes WHERE cedula = '{cedula}'"`, la consulta se convierte en *"trae a todos"*. Con un ORM eso no puede pasar porque el valor se envía separado de la instrucción.

## 4.4 `database.py` — la conexión

```python
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)
```

- **`engine`** (motor): el objeto que sabe **cómo conectarse** a la base de datos. Se crea una vez.
- **`check_same_thread: False`**: SQLite, por defecto, solo deja usar una conexión en el hilo que la creó. FastAPI atiende las funciones normales (`def`) en un **grupo de hilos** (*threadpool*), así que hay que desactivar esa restricción.
- `... if condición else ...` es el **operador ternario** (Parte 5).

```python
@event.listens_for(engine, "connect")
def _activar_foreign_keys(dbapi_conn, _):
    if "sqlite" in settings.database_url:
        dbapi_conn.execute("PRAGMA foreign_keys=ON")
```

- **`@event.listens_for(...)`**: un **decorador** que registra la función para que se ejecute **cada vez que se abre una conexión**. Es el patrón *Observer* (escuchar eventos).
- SQLite, por razones históricas, **no verifica las claves foráneas** a menos que se le pida con `PRAGMA foreign_keys=ON`. Sin esto podríamos crear una asistencia para una clase inexistente.
- El parámetro `_` significa "recibo este argumento pero no lo uso".

```python
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
```

- **`sessionmaker`** es una **fábrica de sesiones**. Una **sesión** es una "conversación" con la base de datos: acumulas cambios (`add`, modificar atributos, `delete`) y al final los confirmas con `commit()` o los descartas con `rollback()`.
- **`autoflush=False`**: no enviar cambios pendientes a la BD automáticamente antes de cada consulta; los enviamos al hacer `commit()`. Comportamiento más predecible.
- **`expire_on_commit=False`**: después del `commit()`, los objetos **conservan sus valores** en memoria. Así podemos hacer `db.commit()` y luego `return seccion` sin que SQLAlchemy vuelva a consultar la base.

```python
class Base(DeclarativeBase):
    """Clase base de todos los modelos ORM."""
```

Todas las clases que hereden de `Base` se convierten en tablas. `Base.metadata` es el "catálogo" de todas ellas; `main.py` lo usa para crearlas.

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Esta es una **dependencia de FastAPI** (se explica en 4.10). Lo importante ahora:

- **`yield`** en lugar de `return` convierte la función en un **generador**: entrega la sesión, **se pausa**, FastAPI ejecuta la ruta, y cuando la ruta termina la función **continúa** desde el `yield`.
- **`try / finally`**: el bloque `finally` se ejecuta **siempre**, haya error o no. Garantiza que la sesión se cierre. Resultado: **una sesión por petición**, abierta y cerrada automáticamente.

## 4.5 `models.py` — las tablas como clases (POO + ORM)

### El diagrama entidad-relación

```mermaid
erDiagram
    USUARIO ||--o{ SECCION : "coordina"
    USUARIO |o--o{ SECCION : "dicta"
    SECCION ||--o{ INSCRIPCION : "tiene"
    ESTUDIANTE ||--o{ INSCRIPCION : "está en"
    SECCION ||--o{ CLASE : "tiene"
    CLASE ||--o{ ASISTENCIA : "registra"
    ESTUDIANTE ||--o{ ASISTENCIA : "marca"

    USUARIO {
        int id PK
        string usuario UK
        string nombre
        string clave_hash
        string rol
    }
    SECCION {
        int id PK
        string codigo UK
        string asignatura
        int coordinador_id FK
        int docente_id FK "puede ser NULL"
    }
    ESTUDIANTE {
        int id PK
        string cedula UK
        string nombres
        string apellidos
    }
    INSCRIPCION {
        int id PK
        int seccion_id FK
        int estudiante_id FK
    }
    CLASE {
        int id PK
        int seccion_id FK
        date fecha
        string tema
        bool abierta
        string secreto
        datetime creada_en
    }
    ASISTENCIA {
        int id PK
        int clase_id FK
        int estudiante_id FK
        datetime marcada_en
    }
```

(Si su visor no dibuja *Mermaid*, el mismo diagrama en ASCII está al inicio de `models.py`.)

**¿Por qué "Clase" y no "Sesión"?** Porque en SQLAlchemy "sesión" ya significa otra cosa (la conversación con la BD). Llamar `Clase` a cada encuentro evita confusiones.

### El `Enum` de roles

```python
class Rol(str, enum.Enum):
    COORDINADOR = "coordinador"
    DOCENTE = "docente"
```

- Un **Enum** (enumeración) es un conjunto **cerrado** de valores posibles. Evita errores de tipeo: si escriben `Rol.DOSENTE`, Python da error de inmediato; si usaran el texto `"dosente"`, el error pasaría desapercibido.
- **Herencia múltiple `(str, enum.Enum)`**: cada miembro **es también un `str`**. Así `Rol.DOCENTE == "docente"` es `True` y se convierte a JSON como `"docente"` sin esfuerzo.

### Anatomía de un modelo

```python
class Estudiante(Base):
    __tablename__ = "estudiantes"

    id: Mapped[int] = mapped_column(primary_key=True)
    cedula: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nombres: Mapped[str] = mapped_column(String(100))
    apellidos: Mapped[str] = mapped_column(String(100))

    @property
    def nombre_completo(self) -> str:
        return f"{self.apellidos}, {self.nombres}"
```

Línea por línea:

- **`class Estudiante(Base)`**: herencia. Al heredar de `Base`, SQLAlchemy sabe que esta clase es una tabla.
- **`__tablename__ = "estudiantes"`**: nombre de la tabla en SQL. Los nombres con doble guion bajo al inicio y al final (*dunder*) son "nombres especiales" que una librería o Python reconocen.
- **`id: Mapped[int]`**: *anotación de tipo*. Dice "este atributo, mapeado a una columna, es un `int`". SQLAlchemy 2.0 **lee estas anotaciones** para decidir el tipo SQL y si admite `NULL`.
- **`mapped_column(primary_key=True)`**: detalles de la columna. `primary_key=True` la hace clave primaria; SQLite la autoincrementa sola (1, 2, 3…).
- **`String(20)`**: texto de máximo 20 caracteres (`VARCHAR(20)`).
- **`unique=True, index=True`**: no se repite y se busca rápido.
- **`@property`**: convierte el método en un **atributo calculado**. Se usa `estudiante.nombre_completo` **sin paréntesis**. No se guarda en la base: se calcula cada vez. Es **encapsulamiento**: la regla "apellidos, nombres" vive en un solo lugar.

El SQL que SQLAlchemy genera para esta clase es, aproximadamente:

```sql
CREATE TABLE estudiantes (
    id INTEGER NOT NULL PRIMARY KEY,
    cedula VARCHAR(20) NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL
);
CREATE UNIQUE INDEX ix_estudiantes_cedula ON estudiantes (cedula);
```

### Claves foráneas y columnas opcionales

```python
class Seccion(Base):
    ...
    coordinador_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    docente_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
```

- **`ForeignKey("usuarios.id")`**: esta columna debe contener un `id` que exista en la tabla `usuarios`.
- **`int | None`**: "un entero **o** nada". Una sección puede estar **sin docente** (por ejemplo, si se eliminó el docente). En SQL eso es `NULL`.

### Relaciones: navegar entre objetos

```python
    coordinador: Mapped[Usuario] = relationship(foreign_keys=[coordinador_id])
    docente: Mapped[Usuario | None] = relationship(
        back_populates="secciones_dictadas", foreign_keys=[docente_id]
    )
    inscripciones: Mapped[list["Inscripcion"]] = relationship(
        back_populates="seccion", cascade="all, delete-orphan"
    )
    clases: Mapped[list["Clase"]] = relationship(
        back_populates="seccion", cascade="all, delete-orphan", order_by="Clase.fecha"
    )
```

- **`relationship(...)`** no crea columnas: crea un **atajo de navegación**. Con `seccion.docente` obtenemos el objeto `Usuario` completo, y con `seccion.clases` la lista de clases. SQLAlchemy hace el `SELECT` por nosotros cuando accedemos al atributo (carga **perezosa**, *lazy loading*).
- **`foreign_keys=[...]`**: `Seccion` tiene **dos** claves foráneas hacia `usuarios` (coordinador y docente). Hay que decirle a SQLAlchemy cuál usar para cada relación; si no, no sabría.
- **`back_populates="seccion"`**: conecta las dos puntas. `Seccion.clases` y `Clase.seccion` son la misma relación vista desde cada lado; si agregas una clase a `seccion.clases`, automáticamente `clase.seccion` apunta a esa sección.
- **`list["Inscripcion"]`** con comillas: la clase `Inscripcion` se define **más abajo** en el archivo. Las comillas son una *referencia adelantada* (*forward reference*): "esto se resolverá después".
- **`cascade="all, delete-orphan"`**: si borras la sección, **se borran también** sus inscripciones y sus clases; y si sacas una inscripción de la lista, se borra de la base (quedó "huérfana").
- **`order_by="Clase.fecha"`**: `seccion.clases` siempre viene ordenada por fecha.

```python
    @property
    def estudiantes(self) -> list[Estudiante]:
        return [i.estudiante for i in self.inscripciones]
```

Una propiedad que recorre la tabla puente y devuelve directamente los estudiantes: una *comprensión de lista* (Parte 5).

### La tabla puente y las restricciones únicas compuestas

```python
class Inscripcion(Base):
    __tablename__ = "inscripciones"
    __table_args__ = (UniqueConstraint("seccion_id", "estudiante_id"),)

    seccion_id: Mapped[int] = mapped_column(ForeignKey("secciones.id", ondelete="CASCADE"))
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiantes.id"))
```

- **`UniqueConstraint("seccion_id", "estudiante_id")`**: el **par** no se puede repetir. Un estudiante puede estar en muchas secciones, pero **no dos veces en la misma**.
- **`(algo,)`** con coma final: es una **tupla de un solo elemento**. Sin la coma, los paréntesis serían solo agrupación y no una tupla.
- **`ondelete="CASCADE"`**: lo mismo que `cascade` del ORM, pero a nivel de la **base de datos**: si se borra la sección directamente con SQL, la base borra sus inscripciones. Doble protección.

`Asistencia` tiene `UniqueConstraint("clase_id", "estudiante_id")`. **Esta línea es la que garantiza que nadie marque dos veces**, incluso si el mismo alumno pulsa "Marcar" dos veces muy rápido y las dos peticiones llegan al mismo tiempo. Validar en Python no bastaría: entre "verificar" y "guardar" podría colarse la otra petición (*condición de carrera*). La base de datos es la última palabra.

### Valores por defecto inteligentes en `Clase`

```python
    fecha: Mapped[date] = mapped_column(Date, default=hoy)
    tema: Mapped[str] = mapped_column(String(200), default="")
    abierta: Mapped[bool] = mapped_column(default=True)
    secreto: Mapped[str] = mapped_column(String(64), default=lambda: secrets.token_hex(16))
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
```

Fíjense en **`default=hoy`** — **sin paréntesis**. No le pasamos *la fecha de hoy*, le pasamos **la función** `hoy`. SQLAlchemy la llamará **en el momento de insertar** cada clase. Si pusiéramos `default=hoy()`, la fecha se calcularía una sola vez al arrancar el servidor y todas las clases de los días siguientes quedarían con esa fecha vieja. En Python **las funciones son valores** que se pueden pasar como argumento.

Lo mismo con **`default=lambda: secrets.token_hex(16)`**: una función anónima que genera un **secreto aleatorio distinto para cada clase** (32 caracteres hexadecimales). Con ese secreto se calculan los códigos del QR.

**`DateTime(timezone=True)`** + `ahora()` que devuelve la hora en UTC: las horas exactas se guardan en UTC (estándar internacional) y la fecha "del día de clase" en hora de Caracas.

## 4.6 `schemas.py` — la forma del JSON (Pydantic)

### El problema

Recuerden `float(input("Ingrese el precio..."))` en `recursiva_compra.py`: si el usuario escribía `abc`, el programa **explotaba**. Y si escribía `-5`, tuvieron que validar a mano con `if precio < 0`. En una API llegan miles de peticiones, algunas malformadas a propósito. Validar todo a mano con `if` sería larguísimo.

### La solución: Pydantic

**Pydantic** valida datos a partir de **clases con tipos**. Declaras *cómo debe ser* el dato y Pydantic se encarga del resto:

```python
class SeccionIn(BaseModel):
    codigo: str = Field(min_length=1, max_length=20, pattern=r"^[A-Za-z0-9\-]+$")
    asignatura: str = Field(min_length=2, max_length=120)
    docente_id: int | None = None
```

Si llega `{"codigo": "A B!", "asignatura": "X"}`, FastAPI **no llega a ejecutar** nuestra función: responde automáticamente **422** con el detalle de qué falló (`codigo` no cumple el patrón; `asignatura` es muy corta). Además:

- Si mandan `"docente_id": "5"` (texto), Pydantic lo **convierte** a `5`.
- Campos que **no** están en el esquema se **ignoran** (lo prueba `test_alcance_solo_docentes`: aunque manden `"rol": "coordinador"`, `DocenteIn` no tiene ese campo y el usuario se crea como docente).

**`Field(...)`** añade reglas:

| Regla                                                                                                                                                     | Significado                     |
| --------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- |
| `min_length` / `max_length`                                                                                                                           | Largo mínimo/máximo del texto |
| `pattern=r"^[A-Za-z0-9\-]+$"` | **Expresión regular**: solo letras, números y guiones, de principio (`^`) a fin (`$`), al menos uno (`+`) |                                 |
| `default=None`                                                                                                                                          | Valor si no lo mandan           |

### Entrada (`In`) y salida (`Out`) separadas

```python
class UsuarioOut(_ORM):
    id: int
    usuario: str
    nombre: str
    rol: Rol
```

`UsuarioOut` **no tiene `clave_hash`**. Aunque el objeto `Usuario` de la base sí la tenga, al responder FastAPI **filtra** los campos según este esquema. Nunca filtraremos por accidente un hash de contraseña ni el `secreto` de una clase. Esta separación se llama patrón **DTO** (*Data Transfer Object*): objetos solo para transportar datos hacia/desde afuera, distintos de las entidades internas.

```python
class _ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)
```

Una **clase base** de la que heredan los esquemas de salida. `from_attributes=True` le permite a Pydantic **leer un objeto de SQLAlchemy** (con atributos `.id`, `.nombre`) en vez de exigir un diccionario. Gracias a eso una ruta puede hacer `return seccion` (objeto ORM) y FastAPI lo convierte a `SeccionOut` y luego a JSON. El guion bajo inicial en `_ORM` indica "uso interno de este módulo".

**Composición de esquemas:** `SeccionOut` tiene `docente: UsuarioOut | None`. Pydantic convierte también el objeto anidado. Por eso el JSON de una sección trae el docente completo adentro.

## 4.7 `security.py` — contraseñas, tokens y roles

### Contraseñas: nunca se guardan, se guarda su *hash*

Un **hash** es una función de **un solo sentido**: de la clave sale una "huella" de longitud fija, pero de la huella **no se puede** sacar la clave. Para verificar, se vuelve a calcular la huella de lo que escribió el usuario y se compara.

> **Hash ≠ cifrado.** Lo cifrado se puede descifrar con la llave. Un hash **no** se "deshashea". Si roban la base de datos, no obtienen las claves.

```python
_ITERACIONES = 200_000

def hashear_clave(clave: str) -> str:
    sal = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", clave.encode(), sal, _ITERACIONES)
    return f"{sal.hex()}${digest.hex()}"
```

- **Sal (*salt*)**: 16 bytes aleatorios distintos para cada usuario. Si dos docentes usan la clave `123456`, sus hashes serán **distintos**. Esto inutiliza las "tablas arcoíris" (listas precalculadas de hashes de claves comunes).
- **PBKDF2-HMAC-SHA256 con 200 000 iteraciones**: aplica el hash 200 000 veces. Para un usuario legítimo tarda una fracción de segundo; para un atacante que quiera probar mil millones de claves es carísimo. Es **lento a propósito**. Viene incluido en Python (`hashlib`), no hay que instalar nada, y lo recomienda OWASP.
- **`clave.encode()`**: convierte el texto (`str`) en **bytes**; las funciones criptográficas trabajan con bytes.
- Se guarda como `"sal_en_hex$hash_en_hex"` para poder separar ambos al verificar.

```python
def verificar_clave(clave: str, guardado: str) -> bool:
    sal_hex, hash_hex = guardado.split("$")
    digest = hashlib.pbkdf2_hmac("sha256", clave.encode(), bytes.fromhex(sal_hex), _ITERACIONES)
    return hmac.compare_digest(digest.hex(), hash_hex)
```

- **`sal_hex, hash_hex = guardado.split("$")`**: *desempaquetado*: `split` devuelve una lista de dos elementos y se asignan a dos variables a la vez.
- **`hmac.compare_digest`** compara en **tiempo constante**. Un `==` normal se detiene en la primera letra distinta, y midiendo microsegundos un atacante podría ir adivinando letra por letra (*ataque de temporización*). `compare_digest` siempre tarda lo mismo.

### JWT: el "carnet" del usuario

Después del login, el servidor no guarda ninguna "sesión". En cambio, le entrega al usuario un **JWT** (*JSON Web Token*): un texto firmado que dice quién es. Es como un **carnet plastificado con sello**: cualquiera puede leerlo, pero nadie puede falsificarlo sin el sello.

Un JWT tiene tres partes separadas por puntos:

```text
eyJhbGciOiJIUzI1NiJ9 . eyJzdWIiOiIyIiwicm9sIjoiZG9jZW50ZSIsImV4cCI6MTc5...} . 4f9c2a...
      CABECERA                      CONTENIDO (payload)                       FIRMA
  {"alg":"HS256"}         {"sub":"2","rol":"docente","exp":17...}     HMAC(cabecera.contenido, SECRET_KEY)
```

```python
def crear_token(usuario: Usuario) -> str:
    payload = {
        "sub": str(usuario.id),          # "subject": de quién es el token
        "rol": usuario.rol.value,        # "docente" o "coordinador"
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.token_horas),  # vence en 12 h
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")
```

- **`sub`** y **`exp`** son nombres estándar de JWT. PyJWT **verifica `exp` automáticamente**: un token vencido es rechazado.
- **HS256** = firma HMAC con SHA-256 usando `SECRET_KEY`. Si alguien cambia `"rol":"docente"` por `"coordinador"`, la firma ya no coincide y el token se rechaza. **Por eso `SECRET_KEY` debe ser secreta y cambiarse en producción.**
- **Importante:** el contenido del JWT está codificado en Base64, **no cifrado**. Cualquiera puede leerlo. Por eso **nunca** se ponen datos secretos dentro del token.

El frontend guarda el token y lo envía en cada petición con la cabecera:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
```

*Bearer* significa "portador": quien porta el token, es el usuario.

### Las dependencias de seguridad

```python
_bearer = HTTPBearer(auto_error=False)

def usuario_actual(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No autenticado")
    try:
        payload = jwt.decode(cred.credentials, settings.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o vencido")
    usuario = db.get(Usuario, int(payload["sub"]))
    if usuario is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario no existe")
    return usuario
```

Paso a paso:

1. `HTTPBearer` extrae el token de la cabecera `Authorization`. Con `auto_error=False` devuelve `None` si no hay token (en vez de lanzar su propio error), para que **nosotros** respondamos 401 con nuestro mensaje.
2. `jwt.decode` verifica la firma y la expiración. Si algo falla lanza una excepción de la familia `PyJWTError`, que capturamos con `try/except`.
3. `algorithms=["HS256"]` (lista explícita) evita un ataque conocido en el que el atacante cambia el algoritmo del token a `none`.
4. `db.get(Usuario, id)` busca por clave primaria. Si el usuario fue eliminado después de recibir su token, también se rechaza.
5. **`raise HTTPException(...)`**: lanzar esta excepción **corta la ejecución** y FastAPI la convierte en una respuesta HTTP con ese código y `{"detail": "mensaje"}`.

```python
def solo_coordinador(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
    if usuario.rol != Rol.COORDINADOR:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo el coordinador puede hacer esto")
    return usuario
```

Una dependencia **que depende de otra**: primero se averigua quién es (401 si no se sabe) y luego se verifica el rol (403 si no es coordinador). Esto se llama **cadena de dependencias**.

## 4.8 `services/` — la lógica de negocio pura

Esta carpeta es el **corazón**: los algoritmos del proyecto. Ningún archivo de aquí importa nada de HTTP (salvo tipos). Por eso se prueban fácil.

### 4.8.1 `codigo_qr.py` — el QR rotativo (anti-foto)

**Problema:** un QR fijo se fotografía y se reenvía por WhatsApp.

**Idea:** la misma que usa **Google Authenticator** (el algoritmo **TOTP**, *Time-based One-Time Password*): el código depende **del tiempo**, cambia cada 30 s y solo lo puede calcular quien conoce el secreto.

```python
class GeneradorCodigoQR:
    def __init__(self, ventana_segundos: int = 30, ventanas_tolerancia: int = 1):
        self.ventana_segundos = ventana_segundos
        self.ventanas_tolerancia = ventanas_tolerancia

    def _ventana(self, instante: float | None = None) -> int:
        return int((instante if instante is not None else time.time()) // self.ventana_segundos)
```

- **`time.time()`** devuelve los segundos transcurridos desde el 1 de enero de 1970 (el *epoch* de Unix), p. ej. `1795000000.42`.
- **`//`** es la **división entera**. `1795000000 // 30 = 59833333`. Ese número es la **ventana**: es el mismo durante 30 segundos y luego sube en 1. Es como el número de "turno" de 30 segundos.
- **`instante`** opcional: en producción usamos la hora real; en los tests le pasamos un instante fijo para que la prueba sea **determinista** (siempre da el mismo resultado).

```python
    @staticmethod
    def _calcular(secreto: str, clase_id: int, ventana: int) -> str:
        mensaje = f"{clase_id}:{ventana}".encode()
        return hmac.new(secreto.encode(), mensaje, hashlib.sha256).hexdigest()[:8]
```

- **HMAC** (*Hash-based Message Authentication Code*): un hash que mezcla un **mensaje** con una **clave secreta**. Sin el secreto es imposible calcular el resultado correcto.
- El mensaje es `"15:59833333"` (clase 15, ventana 59833333). Cada clase tiene su propio secreto (generado en `models.py`), así que el código de una clase no sirve para otra.
- **`.hexdigest()[:8]`**: el resultado en hexadecimal (64 caracteres) recortado a los **primeros 8** con un *slice*. 8 caracteres hex = 16⁸ ≈ **4 300 millones** de combinaciones: imposible adivinar en 30 segundos.
- **`@staticmethod`**: el método **no usa `self`**; es una función que vive dentro de la clase por organización.

```python
    def segundos_restantes(self, instante: float | None = None) -> int:
        t = instante if instante is not None else time.time()
        return self.ventana_segundos - int(t % self.ventana_segundos)
```

**`%`** es el **módulo** (el resto de la división). Si `t % 30 = 12`, han pasado 12 s de la ventana actual y quedan `30 - 12 = 18`.

```python
    def es_valido(self, secreto, clase_id, codigo, instante=None) -> bool:
        actual = self._ventana(instante)
        for v in range(actual - self.ventanas_tolerancia, actual + 1):
            if hmac.compare_digest(self._calcular(secreto, clase_id, v), codigo):
                return True
        return False
```

- Prueba la ventana **anterior** y la **actual** (`range(actual - 1, actual + 1)` produce dos números). Así, si Ana escaneó en el segundo 29 y envió en el segundo 31, igual vale. En total, un código sirve **entre 30 y 60 segundos**.
- **El servidor no guarda los códigos**: los **recalcula** cada vez. No hay tabla de códigos, ni limpieza de códigos viejos. Complejidad **O(1)**.

**Ejemplo numérico (el mismo del test):**

| Instante      | Ventana    | ¿El código generado en `t=1 000 000` es válido? |
| ------------- | ---------- | ---------------------------------------------------- |
| `1 000 000` | `33 333` | ✅ es la ventana actual                              |
| `1 000 030` | `33 334` | ✅ la anterior (33 333) está tolerada               |
| `1 000 060` | `33 335` | ❌ se aceptan 33 334 y 33 335; la 33 333 ya no       |

### 4.8.2 `matricula.py` — leer CSV o Excel

El coordinador sube un archivo con `nombres, apellidos, cedula`. Los archivos reales son **sucios**: encabezados con mayúsculas y acentos ("Cédula"), separados por `;` porque Excel en español así los guarda, codificación Latin-1, cédulas escritas `V-12.345.678`, filas vacías, filas duplicadas. Este servicio limpia todo eso.

```python
@dataclass
class FilaMatricula:
    cedula: str
    nombres: str
    apellidos: str

@dataclass
class ResultadoLectura:
    filas: list[FilaMatricula] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)
```

**`field(default_factory=list)`**: "si no me dan valor, crea **una lista nueva** para cada objeto". No se puede poner `= []` porque todas las instancias **compartirían la misma lista** (un error clásico de Python con valores por defecto mutables; `dataclass` incluso lo prohíbe). Fíjense que en `recursiva_compra.py` ya resolvieron este mismo problema con `lista_articulos=None` y `if lista_articulos is None: lista_articulos = []`. ¡Es exactamente el mismo concepto!

```python
    @staticmethod
    def normalizar_cedula(valor) -> str:
        if isinstance(valor, float):   # Excel a veces guarda 12345678 como 12345678.0
            valor = int(valor)
        return re.sub(r"\D", "", str(valor or ""))
```

- **`re.sub(r"\D", "", texto)`**: expresión regular. `\D` = "cualquier carácter que **no** sea dígito". Se reemplazan todos por nada. `"V-12.345.678"` → `"12345678"`.
- **`r"..."`** (*raw string*): la barra invertida se toma literal, sin que Python la interprete.
- **`valor or ""`**: si `valor` es `None` o vacío, usa `""`. El `or` devuelve el primer valor "verdadero".
- **`isinstance(valor, float)`**: pregunta el tipo. `str(12345678.0)` daría `"12345678.0"` y la normalización dejaría `"123456780"` (¡un cero de más!), por eso se convierte primero a `int`.

```python
    def _filas_crudas(self, nombre_archivo: str, contenido: bytes) -> list[list]:
        if nombre_archivo.lower().endswith((".xlsx", ".xlsm")):
            libro = load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
            return [list(f) for f in libro.active.iter_rows(values_only=True)]
        try:
            texto = contenido.decode("utf-8-sig")
        except UnicodeDecodeError:
            texto = contenido.decode("latin-1")
        dialecto = csv.Sniffer().sniff(texto.splitlines()[0], delimiters=",;\t")
        return list(csv.reader(io.StringIO(texto), dialecto))
```

- **`endswith((".xlsx", ".xlsm"))`**: acepta una **tupla** y devuelve `True` si termina en cualquiera.
- **`io.BytesIO(contenido)`**: el archivo subido llega como `bytes` en memoria; `BytesIO` lo envuelve para que **parezca un archivo** abierto. Así `openpyxl` lo lee sin guardarlo en disco.
- **`read_only=True`**: modo rápido y de poca memoria; **`data_only=True`**: si una celda tiene fórmula, trae el **valor calculado**, no la fórmula.
- **`"utf-8-sig"`**: UTF-8 que además quita el **BOM** (un carácter invisible que Excel pone al inicio). Si falla, se intenta **Latin-1** (lo que usa Excel en Windows en español). Este patrón "intenta, y si falla, plan B" usa `try/except`.
- **`csv.Sniffer().sniff(...)`**: "olfatea" la primera línea y adivina si el separador es `,`, `;` o tabulador (`\t`).

```python
    def leer(self, nombre_archivo: str, contenido: bytes) -> ResultadoLectura:
        ...
        encabezado = [self._normalizar_encabezado(c) for c in filas[0]]
        faltantes = [c for c in COLUMNAS if c not in encabezado]
        if faltantes:
            resultado.errores.append(f"Faltan columnas: {', '.join(faltantes)}")
            return resultado
        idx = {c: encabezado.index(c) for c in COLUMNAS}

        por_cedula: dict[str, FilaMatricula] = {}
        for numero, fila in enumerate(filas[1:], start=2):
            if not any(fila):
                continue
            celda = lambda c: fila[idx[c]] if idx[c] < len(fila) else ""
            cedula = self.normalizar_cedula(celda("cedula"))
            ...
            por_cedula[cedula] = FilaMatricula(cedula, nombres.title(), apellidos.title())

        resultado.filas = list(por_cedula.values())
        return resultado
```

- **Encabezados en cualquier orden**: `idx` es un **diccionario** `{"nombres": 0, "apellidos": 1, "cedula": 2}` que dice en qué columna está cada dato.
- **`enumerate(filas[1:], start=2)`**: recorre desde la segunda fila (`[1:]` salta el encabezado) y numera empezando en 2, para que el mensaje "Fila 6: datos incompletos" coincida con el número de fila que el coordinador ve en Excel.
- **`any(fila)`**: `True` si al menos una celda tiene algo. Si todas están vacías, `continue` salta a la siguiente.
- **`celda = lambda c: ...`**: una función pequeña definida en el momento, para no repetir "si la columna existe en esta fila, dámela; si no, vacío".
- **`.title()`**: `"ana maria"` → `"Ana Maria"`.
- **Diccionario `por_cedula`**: si la misma cédula aparece dos veces, la segunda **sobrescribe** a la primera. Elimina duplicados en **O(1)** por fila. Con una lista habría que buscar en toda la lista cada vez (O(n) por fila, O(n²) en total).
- **Los errores no detienen la carga**: las filas buenas se procesan y las malas se informan. Mejor experiencia para el coordinador.

### 4.8.3 `estadisticas.py` — porcentajes en tiempo lineal

Con **E** estudiantes, **C** clases y **A** asistencias de una sección:

- % de un estudiante = asistencias del estudiante / C × 100
- % de una clase = presentes / E × 100
- % de la sección = A / (E × C) × 100
- **En riesgo** si % del estudiante < **75 %**

**La forma ingenua** sería: por cada estudiante, consultar a la base cuántas asistencias tiene. Con 40 estudiantes son 40 consultas (más una para la lista): el famoso **problema N+1**, que hace lentas a muchísimas aplicaciones reales.

**Nuestra forma:**

```python
        pares = self.db.execute(
            select(Asistencia.clase_id, Asistencia.estudiante_id)
            .join(Clase)
            .where(Clase.seccion_id == seccion.id)
        ).all()
        inscritos = {e.id for e in estudiantes}   # set: pertenencia en O(1)
        por_estudiante: Counter[int] = Counter()
        por_clase: Counter[int] = Counter()
        for clase_id, estudiante_id in pares:
            if estudiante_id in inscritos:
                por_estudiante[estudiante_id] += 1
                por_clase[clase_id] += 1
```

1. **Una sola consulta** trae todos los pares `(clase, estudiante)` de la sección. El SQL equivalente es:
   ```sql
   SELECT asistencias.clase_id, asistencias.estudiante_id
   FROM asistencias JOIN clases ON clases.id = asistencias.clase_id
   WHERE clases.seccion_id = 3;
   ```
2. **Un solo recorrido** llena dos **`Counter`**. Un `Counter` es un diccionario que cuenta: si la clave no existe, vale 0, así que `+= 1` funciona sin inicializar. Es la versión profesional de los contadores `contador_peatones += 1` de `recursiva_sensor.py`, pero con **un contador por cada estudiante** en un solo objeto.
3. **`for clase_id, estudiante_id in pares`**: desempaquetado de tuplas dentro del `for`.
4. El `set` `inscritos` ignora asistencias de alumnos que fueron **retirados** de la sección después.

Complejidad: **O(A + E + C)**, lineal. Es la diferencia entre 1 consulta y 41.

```python
                porcentaje=(p := _pct(por_estudiante[e.id], C)),
                en_riesgo=C > 0 and p < UMBRAL_RIESGO,
```

**`:=`** es el **operador morsa** (*walrus*, por los colmillos): calcula el valor, **lo guarda en `p`** y lo usa ahí mismo. En la línea siguiente reutilizamos `p` sin calcular dos veces. `C > 0 and ...` evita marcar "en riesgo" a todos cuando aún no ha habido clases.

```python
def _pct(parte: int, total: int) -> float:
    return round(parte * 100 / total, 1) if total else 0.0
```

Evita la **división entre cero** (sección sin clases o sin estudiantes) y redondea a un decimal.

Los resultados son **dataclasses** (`EstadisticaEstudiante`, `ResumenSeccion`, `ReporteSeccion`, `ResumenGeneral`). FastAPI las sabe convertir a JSON directamente porque las usamos como `response_model`.

**Promedio ponderado del coordinador (`resumen_general`):** si la sección A tiene 5 alumnos con 100 % y la B tiene 40 con 50 %, el promedio simple diría 75 %, lo cual es engañoso. Nosotros sumamos todas las asistencias logradas y las dividimos entre todas las posibles: (5 + 20)/(5 + 40) ≈ 55,6 %. Cada **cupo** pesa lo mismo.

> **Detalle fino honesto:** `resumen_general` reconstruye las asistencias logradas a partir del promedio ya redondeado a un decimal, así que el promedio general puede diferir en décimas del valor exacto. Para un panel es aceptable; si se necesitara exactitud contable, se sumarían los conteos crudos.

**Ejemplo con los datos del test `test_flujo`:** 4 alumnos, 2 clases. Clase 1: marcan 111, 222 y 333. Clase 2: solo 111.

| Cédula | Asistencias | %     | ¿Riesgo? |
| ------- | ----------- | ----- | --------- |
| 111     | 2           | 100,0 | No        |
| 222     | 1           | 50,0  | Sí       |
| 333     | 1           | 50,0  | Sí       |
| 444     | 0           | 0,0   | Sí       |

Sección: 4 asistencias / (4 × 2) = **50,0 %**, con **3** en riesgo. Exactamente lo que verifica el test.

### 4.8.4 `reportes.py` — herencia y polimorfismo de libro

Este archivo es el mejor ejemplo de **POO** del proyecto.

```python
class GeneradorReporte(ABC):
    extension: str
    tipo_mime: str

    @abstractmethod
    def generar(self, reporte: ReporteSeccion) -> bytes: ...

    def nombre_archivo(self, reporte: ReporteSeccion) -> str:
        return f"asistencia_{reporte.resumen.codigo}_{hoy():%Y%m%d}.{self.extension}"
```

- **`ABC`** (*Abstract Base Class*): una **clase abstracta**. No se puede instanciar (`GeneradorReporte()` da error). Existe para **definir un contrato**: "todo generador debe saber `generar`".
- **`@abstractmethod`**: método **obligatorio** para las subclases. Si una subclase no lo implementa, Python no deja crearla.
- **`...`** (*Ellipsis*): equivale a `pass`. "Aquí no hay cuerpo; lo ponen los hijos."
- **`nombre_archivo`** es un método **concreto** heredado por todos: código común escrito una sola vez.
- **`{hoy():%Y%m%d}`**: dentro de un f-string, después de `:` va un **formato**. Para fechas, `%Y%m%d` produce `20261119`. Así el archivo se llama `asistencia_PROG3-A_20261119.pdf`.

```python
class GeneradorExcel(GeneradorReporte):
    extension = "xlsx"
    tipo_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    def generar(self, reporte): ...   # usa openpyxl

class GeneradorPDF(GeneradorReporte):
    extension = "pdf"
    tipo_mime = "application/pdf"
    def generar(self, reporte): ...   # usa fpdf2

GENERADORES: dict[str, GeneradorReporte] = {
    "excel": GeneradorExcel(),
    "pdf": GeneradorPDF(),
}
```

Y en la ruta (`routers/secciones.py`):

```python
    generador = GENERADORES[formato]
    return Response(content=generador.generar(datos), media_type=generador.tipo_mime, ...)
```

**Polimorfismo**: la ruta llama a `generador.generar(datos)` **sin saber** si es Excel o PDF. Cada objeto responde a su manera al mismo mensaje. Comparen con lo que harían sin POO:

```python
# Sin polimorfismo (lo que evitamos):
if formato == "pdf":
    ...50 líneas de PDF...
elif formato == "excel":
    ...50 líneas de Excel...
```

Para agregar CSV mañana: una subclase `GeneradorCSV` y una línea en el diccionario. **La ruta no se toca.** Esto es el principio **abierto/cerrado** (*Open/Closed*, la "O" de SOLID): abierto a extensión, cerrado a modificación. El diccionario `GENERADORES` es una forma sencilla del patrón **Strategy** (estrategia).

Detalles de implementación:

- **Excel**: `Workbook()` crea el libro; `hoja.append([...])` agrega una fila; `Font(bold=True)` pone negrita; `PatternFill("solid", fgColor="F8D7DA")` pinta de rojo claro las filas **en riesgo**; `zip("ABCDEF", (14, 24, ...))` empareja cada columna con su ancho. Se guarda en un `io.BytesIO()` (archivo en memoria) y se devuelven los bytes.
- **PDF**: `FPDF()`, `add_page()`, `set_font("Helvetica", "B", 15)` (B = *bold*), `cell(ancho, alto, texto, border=1, fill=...)` dibuja cada celda de la tabla; `new_x="LMARGIN", new_y="NEXT"` significa "después de esta celda, vuelve al margen izquierdo y baja una línea". `e.apellidos[:28]` recorta textos largos para que quepan.
- Los archivos **nunca tocan el disco**: se generan en memoria y se envían.

## 4.9 FastAPI desde cero (antes de ver los routers)

### ¿Qué es FastAPI?

Un **framework web** (un "esqueleto" de aplicación) para construir APIs en Python. Está construido sobre otras dos piezas:

- **Starlette**: maneja lo de bajo nivel de HTTP (rutas, peticiones, respuestas, archivos estáticos).
- **Pydantic**: valida y convierte datos.

Su idea central: **usar los *type hints* (anotaciones de tipo) de Python para todo**. Con solo mirar la firma de tu función, FastAPI sabe qué datos esperar, los valida, los convierte y genera la documentación.

### ¿Por qué FastAPI y no Flask?

|                            | Flask                          | FastAPI                            |
| -------------------------- | ------------------------------ | ---------------------------------- |
| Validación de JSON        | A mano, o con librerías extra | Automática con Pydantic           |
| Documentación de la API   | A mano, o extensiones          | **Automática** en `/docs` |
| Type hints                 | Opcionales, decorativos        | **Son el mecanismo**         |
| Inyección de dependencias | No trae                        | `Depends` incluido               |
| Asíncrono                 | Limitado                       | Nativo (`async def`)             |

Para una API JSON que consume un frontend React, FastAPI requiere menos código y menos errores.

### Las piezas de FastAPI, con ejemplos del proyecto

#### 1. El decorador de ruta

```python
@router.get("/secciones/{seccion_id}", response_model=SeccionOut)
def ver(seccion_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    return obtener_seccion(db, seccion_id, usuario)
```

**`@router.get(...)`** es un **decorador**: registra la función `ver` para que se ejecute cuando llegue un `GET` a esa ruta. Es el `case` del `match` del que hablamos en la Parte 2.

#### 2. ¿De dónde salen los argumentos? FastAPI los deduce

| Cómo está declarado el parámetro                    | De dónde lo saca FastAPI                                                 | Ejemplo                                              |
| ------------------------------------------------------ | ------------------------------------------------------------------------- | ---------------------------------------------------- |
| Su nombre aparece entre `{}` en la ruta              | **Parámetro de ruta** (*path*)                                   | `seccion_id: int` en `/secciones/{seccion_id}`   |
| Tipo simple (`int`, `str`) que no está en la ruta | **Parámetro de consulta** (*query*), lo que va después de `?` | `c: str = ""` en `/publico/clases/15?c=a3f91c07` |
| Tipo que es un modelo Pydantic                         | **Cuerpo** (*body*) JSON                                          | `datos: SeccionIn`                                 |
| `UploadFile = File(...)`                             | Archivo subido (formulario *multipart*)                                 | `archivo` en la carga de matrícula                |
| `= Depends(funcion)`                                 | **El resultado de otra función** (inyección de dependencias)      | `db: Session = Depends(get_db)`                    |

Y **convierte tipos**: en la URL `/secciones/3`, el `3` es texto, pero como declaramos `seccion_id: int`, llega como entero. Si alguien pide `/secciones/abc`, FastAPI responde **422** sin ejecutar nuestro código.

#### 3. `Query` con validación

```python
def reporte(seccion_id: int, formato: str = Query("pdf", pattern="^(pdf|excel)$"), ...):
```

`formato` viene de `?formato=...`, vale `"pdf"` por defecto, y solo acepta exactamente `pdf` o `excel` (expresión regular). Cualquier otra cosa → 422.

#### 4. `response_model` y `status_code`

- **`response_model=SeccionOut`**: la respuesta se **filtra y valida** con ese esquema. Podemos devolver un objeto ORM y FastAPI se encarga de convertirlo y de **no** incluir campos de más.
- **`status_code=201`**: código por defecto si todo va bien. Para borrar usamos **204** (sin contenido).

#### 5. `HTTPException`

```python
raise HTTPException(status.HTTP_404_NOT_FOUND, "Sección no encontrada")
```

En cualquier punto (incluso dentro de una dependencia o una función auxiliar) se lanza y FastAPI responde con ese código y `{"detail": "Sección no encontrada"}`. `status.HTTP_404_NOT_FOUND` es solo la constante `404` con un nombre legible.

#### 6. Inyección de dependencias (`Depends`) — la sintaxis más "rara"

```python
def crear(datos: SeccionIn,
          db: Session = Depends(get_db),
          coord: Usuario = Depends(solo_coordinador)):
```

Esto **parece** un valor por defecto, pero no lo es. Le dice a FastAPI: *"antes de llamar a `crear`, ejecuta `get_db()` y pásame lo que devuelva como `db`; ejecuta `solo_coordinador()` y pásame el resultado como `coord`"*.

FastAPI arma un **árbol** de dependencias:

```text
crear(datos, db, coord)
├── db    ← get_db()                    abre la sesión (y la cierra al final)
└── coord ← solo_coordinador(usuario)
             └── usuario ← usuario_actual(cred, db)
                           ├── cred ← HTTPBearer   lee la cabecera Authorization
                           └── db   ← get_db()     ¡la MISMA sesión de arriba! (FastAPI la reutiliza en la petición)
```

Ventajas:

- **Seguridad declarativa**: con solo ver la firma de una ruta se sabe quién puede usarla. `Depends(solo_coordinador)` = solo coordinador; `Depends(usuario_actual)` = cualquier usuario autenticado; sin ninguno = **pública** (las rutas del alumno).
- **Cero repetición**: la lógica de "leer token, verificar, buscar usuario" está en un solo lugar.
- **Fácil de probar** (se pueden reemplazar dependencias en los tests).

`_: Usuario = Depends(solo_coordinador)`: el nombre `_` dice "necesito que esta verificación se ejecute, pero no voy a usar el usuario".

#### 7. `def` vs `async def`

- **`def`** normal: FastAPI la ejecuta en un **hilo aparte** del *threadpool*, para no bloquear a las demás peticiones. Es lo que usamos casi siempre, porque SQLAlchemy (en modo normal) es síncrono.
- **`async def`**: se ejecuta en el **bucle de eventos** (*event loop*) y puede usar `await` para esperar cosas sin bloquear. Lo usamos en `cargar_matricula` porque leer el archivo subido es asíncrono: `await archivo.read()`.

> **Analogía:** `async` es un mesonero que, mientras espera que la cocina saque un plato, atiende otras mesas. `def` en el threadpool es tener varios mesoneros.
>
> **Detalle fino:** dentro de `cargar_matricula` (que es `async`) se hacen consultas síncronas a la base. Para un archivo de matrícula de unos cientos de filas es instantáneo; en una aplicación de alto tráfico se usaría la versión asíncrona de SQLAlchemy o se dejaría la función como `def`.

#### 8. `APIRouter`: dividir la API en archivos

```python
router = APIRouter(prefix="/api", tags=["secciones"])
```

Un *router* es un "mini-FastAPI" con un grupo de rutas. `prefix="/api"` se antepone a todas; `tags` las agrupa en la documentación `/docs`. En `main.py` se juntan con `app.include_router(...)`.

#### 9. La documentación automática

FastAPI genera un documento **OpenAPI** (un estándar en JSON que describe toda la API) en `/openapi.json`, y con él dos páginas: **Swagger UI** en `/docs` (para probar) y **ReDoc** en `/redoc` (para leer). Todo sale de los tipos, los esquemas y los *docstrings*. **Nunca se desactualiza**, porque se genera del propio código.

## 4.10 `routers/auth.py` — sesión y docentes

```python
@router.post("/auth/login", response_model=LoginOut)
def login(datos: LoginIn, db: Session = Depends(get_db)):
    usuario = db.scalar(select(Usuario).where(Usuario.usuario == datos.usuario.strip().lower()))
    if usuario is None or not verificar_clave(datos.clave, usuario.clave_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario o clave incorrectos")
    return LoginOut(token=crear_token(usuario), usuario=usuario)
```

- **`select(Usuario).where(Usuario.usuario == ...)`**: así se escribe una consulta en SQLAlchemy 2.0. Equivale a `SELECT * FROM usuarios WHERE usuario = ?`. Ojo: `Usuario.usuario == valor` **no** devuelve `True/False`; SQLAlchemy **sobrecarga** el operador `==` para que construya una condición SQL.
- **`db.scalar(...)`**: ejecuta y devuelve **el primer resultado o `None`**. (`db.scalars(...).all()` devuelve **todos**, como lista.)
- **`.strip().lower()`**: "  Prof " y "prof" son el mismo usuario. *Encadenamiento de métodos*.
- **Mismo mensaje** si el usuario no existe o si la clave está mal: así no le revelamos a un atacante qué usuarios existen.

| Ruta                          | Quién      | Qué hace                                                                          |
| ----------------------------- | ----------- | ---------------------------------------------------------------------------------- |
| `POST /api/auth/login`      | público    | Devuelve token + datos del usuario                                                 |
| `GET /api/auth/yo`          | autenticado | "¿Quién soy?" (el frontend lo usa al recargar la página)                        |
| `PUT /api/auth/clave`       | autenticado | Cambia la propia clave **exigiendo la actual**                               |
| `GET /api/docentes`         | coordinador | Lista docentes ordenados por nombre                                                |
| `POST /api/docentes`        | coordinador | Crea docente (409 si el usuario ya existe). **Siempre** con `rol=DOCENTE`  |
| `PUT /api/docentes/{id}`    | coordinador | Renombra y, si se envía `clave`, la **reinicia** (docente que la olvidó) |
| `DELETE /api/docentes/{id}` | coordinador | Elimina docente; sus secciones quedan **sin asignar**                        |

```python
def _obtener_docente(db: Session, docente_id: int) -> Usuario:
    docente = db.get(Usuario, docente_id)
    if docente is None or docente.rol != Rol.DOCENTE:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Docente no encontrado")
    return docente
```

Esta función impide que se use `/api/docentes/{id}` para editar o borrar **al coordinador** (respondería 404). Lo verifica `test_alcance_solo_docentes`.

```python
    db.execute(update(Seccion).where(Seccion.docente_id == docente.id).values(docente_id=None))
    db.delete(docente)
    db.commit()
```

Una **actualización masiva** (`UPDATE secciones SET docente_id = NULL WHERE docente_id = ?`) y luego el borrado, **en la misma transacción**: si algo falla, no se aplica nada. Así **nunca se pierden asistencias** por borrar a un docente.

## 4.11 `routers/secciones.py` — CRUD, matrícula, estadísticas y reportes

### La regla de acceso

```python
def puede_ver(usuario: Usuario, seccion: Seccion) -> bool:
    if usuario.rol == Rol.COORDINADOR:
        return seccion.coordinador_id == usuario.id
    return seccion.docente_id == usuario.id

def obtener_seccion(db: Session, seccion_id: int, usuario: Usuario) -> Seccion:
    seccion = db.get(Seccion, seccion_id)
    if seccion is None or not puede_ver(usuario, seccion):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sección no encontrada")
    return seccion
```

**Todas** las rutas que reciben un `seccion_id` pasan por `obtener_seccion`. Si un docente pide una sección ajena, recibe **404 y no 403**. ¿Por qué? Porque 403 confirmaría "esa sección existe, pero no es tuya", y eso ya es información. 404 no revela nada. (GitHub hace lo mismo con los repositorios privados.)

Esto protege contra un ataque muy común llamado **IDOR** (*Insecure Direct Object Reference*): cambiar el número en la URL (`/secciones/3` → `/secciones/4`) para ver datos ajenos.

### Listado filtrado por rol

```python
@router.get("/secciones", response_model=list[SeccionOut])
def listar(db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    campo = Seccion.coordinador_id if usuario.rol == Rol.COORDINADOR else Seccion.docente_id
    return db.scalars(select(Seccion).where(campo == usuario.id).order_by(Seccion.codigo)).all()
```

Truco elegante: **guardamos una columna en una variable** (`campo`) y la usamos en la consulta. Una sola ruta sirve a ambos roles.

### Crear y editar

```python
    codigo = datos.codigo.strip().upper()
    if db.scalar(select(Seccion).where(Seccion.codigo == codigo)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una sección con ese código")
```

Normalizamos el código a mayúsculas (`prog3-a` → `PROG3-A`) y respondemos **409 Conflict** si ya existe. Al editar se permite que "el código repetido" sea el de la misma sección (`otra.id != seccion.id`).

```python
    seccion.codigo, seccion.asignatura, seccion.docente_id = codigo, datos.asignatura.strip(), datos.docente_id
```

**Asignación múltiple**: tres atributos en una línea. Cambiar el docente **no** borra clases ni asistencias (lo prueba `test_editar_seccion_conserva_asistencias`).

### Carga de matrícula (la ruta más interesante)

```python
@router.post("/secciones/{seccion_id}/matricula", response_model=ResultadoMatricula)
async def cargar_matricula(seccion_id: int, archivo: UploadFile = File(...),
                           db: Session = Depends(get_db), coord: Usuario = Depends(solo_coordinador)):
    seccion = obtener_seccion(db, seccion_id, coord)
    lectura = LectorMatricula().leer(archivo.filename or "", await archivo.read())

    cedulas = [f.cedula for f in lectura.filas]
    existentes = {e.cedula: e for e in db.scalars(select(Estudiante).where(Estudiante.cedula.in_(cedulas)))}
    ya_en_seccion = {e.cedula for e in seccion.estudiantes}

    agregados = ya_inscritos = 0
    for fila in lectura.filas:
        estudiante = existentes.get(fila.cedula)
        if estudiante is None:
            estudiante = Estudiante(cedula=fila.cedula, nombres=fila.nombres, apellidos=fila.apellidos)
            db.add(estudiante)
        else:
            estudiante.nombres, estudiante.apellidos = fila.nombres, fila.apellidos
        if fila.cedula in ya_en_seccion:
            ya_inscritos += 1
        else:
            seccion.inscripciones.append(Inscripcion(estudiante=estudiante))
            agregados += 1
    db.commit()
    return ResultadoMatricula(agregados=agregados, ya_inscritos=ya_inscritos, errores=lectura.errores)
```

Observen la **división del trabajo**: el *servicio* lee y limpia el archivo (no sabe de base de datos); la *ruta* decide qué guardar.

- **`File(...)`**: los `...` aquí significan **"obligatorio"** (convención de FastAPI/Pydantic).
- **`Estudiante.cedula.in_(cedulas)`**: `WHERE cedula IN ('111', '222', ...)`. **Una sola consulta** para saber cuáles estudiantes ya existen (podrían estar en otra sección).
- **Comprensión de diccionario** `{e.cedula: e for e in ...}`: índice cédula → estudiante, para buscar en **O(1)** con `.get()`.
- **Comprensión de conjunto** `{e.cedula for e in ...}`: las cédulas ya inscritas aquí.
- **`agregados = ya_inscritos = 0`**: asignación encadenada; ambas valen 0.
- **`seccion.inscripciones.append(Inscripcion(estudiante=estudiante))`**: no escribimos `seccion_id` ni `estudiante_id` a mano; la **relación** del ORM los rellena al guardar. Esto es "trabajar con objetos, no con IDs".
- **Un solo `commit()`** al final: si algo falla a mitad, **no se guarda nada a medias**. Es una **transacción**.

Resultado: carga **O(n)** con **2 consultas** en total, sin importar si son 10 o 1 000 filas.

### Retirar a un estudiante

```python
    inscripcion = next((i for i in seccion.inscripciones if i.estudiante_id == estudiante_id), None)
```

**`next(generador, None)`**: devuelve **el primer elemento** que cumple la condición, o `None` si no hay ninguno. Es la forma idiomática de "buscar el primero" en Python, sin escribir un `for` con `break`.

### Reportes: devolver un archivo

```python
    return Response(
        content=generador.generar(datos),
        media_type=generador.tipo_mime,
        headers={"Content-Disposition": f'attachment; filename="{generador.nombre_archivo(datos)}"'},
    )
```

- **`Response`** en vez de un diccionario: aquí no devolvemos JSON sino **bytes de un archivo**.
- **`media_type`** (*tipo MIME*): le dice al navegador qué es (`application/pdf`).
- **`Content-Disposition: attachment; filename="..."`**: le dice al navegador "descárgalo con este nombre" en vez de mostrarlo.

## 4.12 `routers/clases.py` — clases, QR y el marcaje

```python
router = APIRouter(prefix="/api", tags=["clases"])
generador_qr = GeneradorCodigoQR(ventana_segundos=settings.qr_ventana_segundos)
```

Un **único** objeto `GeneradorCodigoQR` para todo el módulo, configurado desde `config.py`.

```python
def obtener_clase(db: Session, clase_id: int, usuario: Usuario) -> Clase:
    clase = db.get(Clase, clase_id)
    if clase is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Clase no encontrada")
    obtener_seccion(db, clase.seccion_id, usuario)  # valida permisos sobre la sección
    return clase
```

**Reutiliza** la regla de acceso de secciones: tienes permiso sobre una clase si lo tienes sobre su sección. Una sola regla, aplicada en todas partes.

### Rutas privadas (docente/coordinador)

| Ruta                                             | Qué hace                                                                                                             |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| `GET /api/secciones/{id}/clases`               | Lista de clases, la más reciente primero (`list(reversed(...))`)                                                   |
| `POST /api/secciones/{id}/clases`              | **Abre** una clase hoy (fecha y secreto los pone el modelo)                                                     |
| `GET /api/clases/{id}`                         | Datos de una clase                                                                                                    |
| `GET /api/clases/{id}/qr`                      | **Código vigente** + segundos restantes + presentes/inscritos. El proyector lo consulta cada 2 s (*polling*) |
| `POST /api/clases/{id}/cerrar` · `/reabrir` | Deja de / vuelve a aceptar marcajes                                                                                   |
| `DELETE /api/clases/{id}`                      | Borra la clase (y sus asistencias, por la cascada)                                                                    |
| `GET /api/clases/{id}/asistentes`              | Toda la sección con `presente: true/false` (lista manual)                                                          |
| `PUT /api/clases/{id}/asistentes/{est}`        | Marca o desmarca a mano                                                                                               |

```python
    presentes = {a.estudiante_id for a in clase.asistencias}  # set → búsqueda O(1)
    filas = [
        AsistenteOut(estudiante_id=e.id, cedula=e.cedula, nombre=e.nombre_completo, presente=e.id in presentes)
        for e in clase.seccion.estudiantes
    ]
    return sorted(filas, key=lambda f: f.nombre)
```

- Un **conjunto** de IDs presentes para que `e.id in presentes` sea **O(1)**. Con una lista sería O(n) por estudiante → O(n²).
- **`sorted(..., key=lambda f: f.nombre)`**: ordena usando como criterio el nombre. Python usa **Timsort**, O(n log n).

### Rutas públicas (el alumno, sin token)

Fíjense: **no tienen `Depends(usuario_actual)`**. Cualquiera puede llamarlas; la seguridad la dan el **código rotativo** y la **matrícula**.

```python
@router.get("/publico/clases/{clase_id}", response_model=InfoClasePublica)
def info_publica(clase_id: int, c: str = "", db: Session = Depends(get_db)):
    ...
        codigo_valido=clase.abierta and generador_qr.es_valido(clase.secreto, clase.id, c),
```

Lo que ve el alumno al abrir el enlace: nombre de la sección, asignatura, fecha y si el código **todavía** es válido (para avisarle "escanéalo de nuevo" antes de que escriba la cédula). El `and` hace **cortocircuito**: si la clase está cerrada, ni siquiera calcula el HMAC.

### El algoritmo de marcaje (la ruta más importante del sistema)

```python
@router.post("/publico/asistencia", response_model=MarcarOut)
def marcar(datos: MarcarIn, db: Session = Depends(get_db)):
    # 1. La clase existe y está abierta
    clase = db.get(Clase, datos.clase_id)
    if clase is None or not clase.abierta:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La clase no está recibiendo asistencias")
    # 2. El código del QR es vigente
    if not generador_qr.es_valido(clase.secreto, clase.id, datos.codigo):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El código QR expiró. Escanéalo de nuevo.")
    # 3. La cédula está inscrita en ESTA sección
    cedula = LectorMatricula.normalizar_cedula(datos.cedula)
    estudiante = db.scalar(
        select(Estudiante).join(Inscripcion)
        .where(Estudiante.cedula == cedula, Inscripcion.seccion_id == clase.seccion_id)
    )
    if estudiante is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tu cédula no está inscrita en esta sección")
    # 4. Guardar; si ya existía, la restricción UNIQUE lo detecta
    db.add(Asistencia(clase_id=clase.id, estudiante_id=estudiante.id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return MarcarOut(mensaje="Ya tenías la asistencia registrada", estudiante=estudiante.nombre_completo)
    return MarcarOut(mensaje="¡Asistencia registrada!", estudiante=estudiante.nombre_completo)
```

Es una **cadena de validaciones con salida temprana** (*guard clauses* / cláusulas de guarda): cada `if` que falla termina la función con un error claro. El "camino feliz" queda al final, sin anidar `if` dentro de `if`.

- **Paso 3**: reutiliza `normalizar_cedula` (el alumno puede escribir `V-28.123.456` o `28123456`). La consulta con **`join`** equivale a:
  ```sql
  SELECT estudiantes.* FROM estudiantes
  JOIN inscripciones ON estudiantes.id = inscripciones.estudiante_id
  WHERE estudiantes.cedula = '28123456' AND inscripciones.seccion_id = 3;
  ```

  Usa los **índices** de `cedula` y es prácticamente instantánea.
- **Paso 4 — "pide perdón, no permiso"** (en Python se llama **EAFP**: *Easier to Ask Forgiveness than Permission*): en lugar de preguntar "¿ya marcó?" y luego insertar (dos pasos donde se puede colar otra petición), **intentamos insertar** y si la base de datos dice "viola UNIQUE" (`IntegrityError`), hacemos **`rollback()`** (deshacer la transacción fallida) y respondemos amablemente. Es correcto incluso con peticiones simultáneas.

## 4.13 `main.py` — donde todo se une

```python
def crear_coordinador_inicial():
    with SessionLocal() as db:
        if db.scalar(select(Usuario).where(Usuario.rol == Rol.COORDINADOR)) is None:
            db.add(Usuario(usuario=settings.admin_usuario, nombre="Coordinador",
                           clave_hash=hashear_clave(settings.admin_clave), rol=Rol.COORDINADOR))
            db.commit()
```

**`with SessionLocal() as db:`**: un **gestor de contexto**. Al salir del bloque, la sesión se cierra sola (como `with open(...)` con archivos). Crea el coordinador solo si no hay ninguno: la función es **idempotente**, se puede ejecutar en cada arranque sin duplicar nada.

```python
@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    Base.metadata.create_all(engine)
    crear_coordinador_inicial()
    yield

app = FastAPI(title="Asistencia QR", version="0.1.0", lifespan=ciclo_de_vida)
```

- **`lifespan`** (ciclo de vida): lo que está **antes del `yield`** se ejecuta **al arrancar** el servidor; lo que estuviera después, **al apagarlo**.
- **`Base.metadata.create_all(engine)`**: crea en la base todas las tablas que falten (`CREATE TABLE IF NOT EXISTS ...`). En proyectos que evolucionan se usaría **Alembic** (migraciones: "scripts" versionados que alteran tablas existentes); para este MVP no hace falta.
- **`@asynccontextmanager`**: decorador que convierte una función con `yield` en un gestor de contexto asíncrono.

```python
app.include_router(auth.router)
app.include_router(secciones.router)
app.include_router(clases.router)

@app.get("/api/salud", tags=["sistema"])
def salud():
    return {"ok": True}
```

Se registran los tres routers. **`/api/salud`** (*health check*) es una práctica profesional: los sistemas de monitoreo y los balanceadores consultan esa ruta para saber si la app está viva.

### Servir el frontend desde el mismo proceso

```python
if (settings.static_dir / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=settings.static_dir / "assets"), name="assets")

    @app.get("/{ruta:path}", include_in_schema=False)
    def spa(ruta: str):
        if ruta.startswith("api/"):
            raise HTTPException(404, "Ruta de API inexistente")
        raiz = settings.static_dir.resolve()
        archivo = (raiz / ruta).resolve()
        if ruta and archivo.is_file() and raiz in archivo.parents:
            return FileResponse(archivo)
        return FileResponse(settings.static_dir / "index.html")
```

- Solo se activa si existe el build de React (en Docker sí; en desarrollo el frontend lo sirve Vite aparte).
- **`app.mount("/assets", StaticFiles(...))`**: sirve los archivos `.js` y `.css` compilados.
- **`/{ruta:path}`**: captura **cualquier** ruta, incluidas las que tienen `/` (el `:path` lo permite). Se declara **al final** para que las rutas de la API, registradas antes, tengan prioridad. **El orden de registro importa.**
- **SPA** (*Single Page Application*): React tiene sus propias "páginas" (`/login`, `/asistir/15`), pero en realidad todas son el mismo `index.html`; React decide qué mostrar según la URL. Por eso cualquier ruta desconocida devuelve `index.html`.
- **`raiz in archivo.parents`**: protección contra **path traversal** (recorrido de directorios). Si alguien pide `/../../etc/passwd`, `.resolve()` calcula la ruta real, y como no está **dentro** de `static/`, no se entrega.
- **`include_in_schema=False`**: esta ruta no aparece en `/docs`.

---

# Parte 5 — Diccionario de sintaxis "nueva y rara"

Todo lo que aparece en el proyecto y probablemente no vieron en clase, de lo más simple a lo más avanzado. Cada entrada dice **dónde** aparece.

### 5.1 Anotaciones de tipo (*type hints*)

```python
def hoy() -> date: ...
def verificar_clave(clave: str, guardado: str) -> bool: ...
token_horas: int = 12
```

`nombre: tipo` dice qué tipo se espera; `-> tipo` dice qué devuelve la función. **Python no los obliga al ejecutar** (si pasas un `int` donde dice `str`, Python no se queja solo), pero:

- el editor te avisa de errores y autocompleta,
- **FastAPI, Pydantic y SQLAlchemy sí los leen** y actúan según ellos.

| Escritura                    | Significado                                | Dónde                     |
| ---------------------------- | ------------------------------------------ | -------------------------- |
| `int \| None`               | un entero **o** `None` (opcional)  | `docente_id: int \| None` |
| `list[str]`                | lista de textos                            | `errores: list[str]`     |
| `dict[str, FilaMatricula]` | diccionario de texto a `FilaMatricula`   | `por_cedula`             |
| `Mapped[int]`              | columna ORM de tipo `int`                | `models.py`              |
| `Counter[int]`             | contador cuyas claves son `int`          | `estadisticas.py`        |
| `list["Seccion"]`          | con comillas: clase definida más adelante | `models.py`              |

### 5.2 f-strings con formato

```python
f"{precio:.2f}"            # ya lo conocen: 2 decimales
f"{hoy():%Y%m%d}"          # fecha con formato: 20261119
f"{hoy():%d/%m/%Y}"        # 19/11/2026
f'attachment; filename="{nombre}"'   # comillas simples por fuera para usar dobles por dentro
```

### 5.3 Literales especiales

| Escritura       | Significado                                                      | Dónde                         |
| --------------- | ---------------------------------------------------------------- | ------------------------------ |
| `200_000`     | El `_` solo separa miles para leer mejor. Es `200000`        | `security.py`                |
| `1_000_000.0` | Igual, con decimales                                             | `test_servicios.py`          |
| `r"\D"`       | *raw string*: la `\` es literal (para regex)                 | `matricula.py`               |
| `b"%PDF"`     | **bytes**, no texto                                        | tests                          |
| `(x,)`        | tupla de **un** elemento (la coma es la que hace la tupla) | `__table_args__`             |
| `...`         | *Ellipsis*: "cuerpo vacío" o "obligatorio" según contexto    | `reportes.py`, `File(...)` |

### 5.4 Operadores

| Operador             | Qué hace                                                       | Ejemplo                              |
| -------------------- | --------------------------------------------------------------- | ------------------------------------ |
| `//`               | división entera                                                | `time.time() // 30`                |
| `%`                | resto (módulo)                                                 | `t % 30`                           |
| `a if cond else b` | **ternario**: `if` en una línea                        | `campo = X if es_coord else Y`     |
| `x or ""`          | "x, o si es vacío/None, `""`"                                | `str(valor or "")`                 |
| `a and b`          | **cortocircuito**: si `a` es falso, `b` ni se evalúa | `clase.abierta and es_valido(...)` |
| `:=`               | **morsa**: asigna y devuelve                              | `(p := _pct(...))`                 |
| `/` con `Path`   | une rutas                                                       | `BASE_DIR / "data"`                |
| `==` en SQLAlchemy | construye una condición SQL, no compara                        | `Usuario.rol == Rol.DOCENTE`       |
| `in`               | pertenencia (O(1) en set/dict)                                  | `e.id in presentes`                |

### 5.5 Desempaquetado y asignaciones múltiples

```python
sal_hex, hash_hex = guardado.split("$")              # lista de 2 → 2 variables
for clase_id, estudiante_id in pares: ...           # tuplas dentro del for
seccion.codigo, seccion.asignatura = codigo, asig   # varias asignaciones en una línea
agregados = ya_inscritos = 0                        # asignación encadenada
```

### 5.6 Comprensiones

Una forma compacta de construir colecciones. Todas se leen igual: **"[esto] para cada elemento en colección (si condición)"**.

```python
[i.estudiante for i in self.inscripciones]                 # LISTA
{e.cedula for e in seccion.estudiantes}                    # CONJUNTO (set)
{e.cedula: e for e in estudiantes_existentes}              # DICCIONARIO
{c: encabezado.index(c) for c in COLUMNAS}                 # DICCIONARIO
[c for c in COLUMNAS if c not in encabezado]               # LISTA con filtro
sum(f.en_riesgo for f in filas_est)                        # GENERADOR: True cuenta como 1
next((i for i in lista if i.estudiante_id == x), None)     # GENERADOR + next: primer elemento o None
```

El equivalente "largo" de la primera, para que vean que no es magia:

```python
resultado = []
for i in self.inscripciones:
    resultado.append(i.estudiante)
```

### 5.7 `lambda`: funciones de una línea sin nombre

```python
sorted(filas, key=lambda f: f.nombre)            # criterio de orden
sorted(est, key=lambda e: (e.apellidos, e.nombres))   # orden por apellido y, si empata, por nombre (tupla)
default=lambda: secrets.token_hex(16)            # función que genera un valor nuevo cada vez
celda = lambda c: fila[idx[c]] if idx[c] < len(fila) else ""
```

`lambda x: expresión` es lo mismo que `def f(x): return expresión`.

### 5.8 Funciones como valores

```python
default=hoy           # pasamos LA FUNCIÓN; SQLAlchemy la llamará después
default=hoy()         # ✗ pasaríamos UNA FECHA fija calculada al arrancar
Depends(get_db)       # pasamos la función para que FastAPI la llame
```

En Python las funciones son objetos: se pueden guardar en variables, pasar como argumentos y devolver.

### 5.9 Decoradores (`@algo`)

Un decorador es una función que **envuelve o registra** otra función o clase. Se escribe encima con `@`.

| Decorador                                    | Qué hace                                                           | Dónde                               |
| -------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------ |
| `@dataclass` / `@dataclass(frozen=True)` | genera `__init__`, `__repr__`, `__eq__` (y la hace inmutable) | `config.py`, `services/`         |
| `@property`                                | método que se usa como atributo (sin `()`)                       | `Estudiante.nombre_completo`       |
| `@staticmethod`                            | método que no recibe `self`                                      | `normalizar_cedula`, `_calcular` |
| `@abstractmethod`                          | método obligatorio para las subclases                              | `GeneradorReporte.generar`         |
| `@router.get(...)`, `@router.post(...)`  | registra una ruta HTTP                                              | routers                              |
| `@event.listens_for(...)`                  | ejecuta la función al ocurrir un evento                            | `database.py`                      |
| `@asynccontextmanager`                     | convierte un generador en gestor de contexto                        | `main.py`                          |
| `@pytest.fixture`                          | declara un recurso reutilizable para tests                          | `conftest.py`                      |

### 5.10 `yield` y generadores

```python
def get_db():
    db = SessionLocal()
    try:
        yield db        # entrega db y se PAUSA aquí
    finally:
        db.close()      # al reanudar (cuando terminó la petición), cierra
```

`return` termina la función. `yield` la **pausa** y la puede reanudar después. Así una sola función puede hacer "preparación → entregar → limpieza". Lo usan `get_db`, `ciclo_de_vida` y las fixtures de pytest.

### 5.11 Gestores de contexto (`with`)

```python
with SessionLocal() as db: ...        # cierra la sesión al salir
with TestClient(app) as c: ...        # arranca y apaga la app (lifespan) en los tests
```

`with` garantiza que algo se **limpie** al salir del bloque, aunque haya un error. Es un `try/finally` empaquetado.

### 5.12 Excepciones: `try / except / finally` y `raise`

```python
try:
    db.commit()
except IntegrityError:      # solo atrapamos ESTE tipo de error, no cualquiera
    db.rollback()

raise HTTPException(404, "...")   # LANZAR un error a propósito para cortar la ejecución
```

- `except TipoDeError:` atrapa solo ese tipo. Atrapar **todo** con `except Exception` solo se hace cuando de verdad cualquier fallo significa lo mismo (lo usamos en `LectorMatricula.leer`: "no se pudo leer el archivo").
- `finally:` se ejecuta siempre.

### 5.13 `async` / `await`

```python
async def cargar_matricula(...):
    contenido = await archivo.read()
```

`async def` define una **corrutina**; `await` significa "espera este resultado, y mientras tanto deja que el servidor atienda otras cosas". Ver 4.9 punto 7.

### 5.14 Herencia, herencia múltiple y clases abstractas

```python
class Estudiante(Base): ...                       # herencia simple
class Rol(str, enum.Enum): ...                    # herencia múltiple: es str Y es Enum
class GeneradorReporte(ABC): ...                  # clase abstracta
class GeneradorPDF(GeneradorReporte): ...         # implementación concreta
class UsuarioOut(_ORM): ...                       # hereda la configuración from_attributes
```

### 5.15 Importaciones relativas y paquetes

```python
from .config import settings          # "." = este mismo paquete (app/)
from ..database import get_db         # ".." = el paquete padre (desde app/routers/ sube a app/)
from .estadisticas import ReporteSeccion   # dentro de services/
```

### 5.16 Convenciones de nombres (no son sintaxis, pero importan)

| Convención      | Significado                                                                   | Ejemplo                                               |
| ---------------- | ----------------------------------------------------------------------------- | ----------------------------------------------------- |
| `MAYUSCULAS`   | constante                                                                     | `UMBRAL_RIESGO`, `COLUMNAS`, `GENERADORES`      |
| `_nombre`      | "privado", de uso interno                                                     | `_ITERACIONES`, `_ventana`, `_ORM`, `_bearer` |
| `_` solo       | variable que no se usa                                                        | `_: Usuario = Depends(...)`                         |
| `__nombre__`   | nombre especial (*dunder*)                                                  | `__tablename__`, `__init__`, `__file__`         |
| `CamelCase`    | clases                                                                        | `CalculadoraEstadisticas`                           |
| `snake_case`   | funciones y variables                                                         | `obtener_seccion`                                   |
| `# noqa: E402` | "linter, ignora la regla E402 en esta línea" (import que no está al inicio) | `conftest.py`                                       |

### 5.17 Expresiones regulares usadas

| Patrón              | Significado                                           |
| -------------------- | ----------------------------------------------------- |
| `\D`               | cualquier carácter que no sea dígito                |
| `^[A-Za-z0-9\-]+$` | de inicio a fin, uno o más: letras, números o guion |
| `^(pdf\|excel)$`    | exactamente `pdf` o exactamente `excel`           |

### 5.18 Métodos útiles que aparecen

| Método                                       | Ejemplo                                         | Resultado                                         |
| --------------------------------------------- | ----------------------------------------------- | ------------------------------------------------- |
| `str.strip()`                               | `"  prof ".strip()`                           | `"prof"`                                        |
| `str.lower()` / `.upper()` / `.title()` | `"ana maria".title()`                         | `"Ana Maria"`                                   |
| `str.removeprefix()`                        | `"sqlite:///x.db".removeprefix("sqlite:///")` | `"x.db"`                                        |
| `str.endswith(tupla)`                       | `"a.xlsx".endswith((".xlsx", ".xlsm"))`       | `True`                                          |
| `str.encode()` / `bytes.decode()`         | `"á".encode()`                               | `b'\xc3\xa1'`                                   |
| `bytes.hex()` / `bytes.fromhex()`         | `b"\x01\xff".hex()`                           | `"01ff"`                                        |
| `", ".join(lista)`                          | `", ".join(["a", "b"])`                       | `"a, b"`                                        |
| `enumerate(x, start=2)`                     | numera desde 2                                  | `(2, fila), (3, fila)...`                       |
| `zip(a, b)`                                 | empareja                                        | `zip("AB", (14, 24))` → `("A",14), ("B",24)` |
| `any(x)`                                    | ¿algún elemento verdadero?                    | `any(["", None, "x"])` → `True`              |
| `reversed(lista)`                           | recorre al revés                               |                                                   |
| `sorted(x, key=...)`                        | copia ordenada                                  |                                                   |
| `isinstance(v, float)`                      | ¿es de este tipo?                              |                                                   |

---

# Parte 6 — Todas las librerías y módulos

## 6.1 Biblioteca estándar (vienen con Python, no se instalan)

| Módulo         | Para qué lo usamos                                                                                              | Archivo(s)                        |
| --------------- | ---------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| `os`          | Leer variables de entorno (`os.getenv`), unir rutas en tests                                                   | `config.py`, `conftest.py`    |
| `dataclasses` | `@dataclass` y `field` para clases de datos                                                                  | `config.py`, `services/`      |
| `datetime`    | `date`, `datetime`, `timedelta`, `timezone`: fechas, horas, vencimiento del token                        | varios                            |
| `zoneinfo`    | `ZoneInfo("America/Caracas")`: zonas horarias                                                                  | `config.py`                     |
| `pathlib`     | `Path`: rutas de archivos orientadas a objetos                                                                 | `config.py`, `database.py`    |
| `contextlib`  | `asynccontextmanager` para el `lifespan`                                                                     | `main.py`                       |
| `enum`        | Enumeración `Rol`                                                                                             | `models.py`                     |
| `secrets`     | Aleatoriedad **criptográfica** (sal, secreto del QR). Nunca usar `random` para seguridad: es predecible | `models.py`, `security.py`    |
| `hashlib`     | `pbkdf2_hmac` (contraseñas) y `sha256`                                                                      | `security.py`, `codigo_qr.py` |
| `hmac`        | `hmac.new` (código QR) y `compare_digest` (comparación en tiempo constante)                                | `security.py`, `codigo_qr.py` |
| `time`        | `time.time()`: segundos desde 1970                                                                             | `codigo_qr.py`                  |
| `collections` | `Counter`: diccionario contador                                                                                | `estadisticas.py`               |
| `csv`         | Leer CSV y detectar separador (`Sniffer`)                                                                      | `matricula.py`                  |
| `io`          | `BytesIO` / `StringIO`: "archivos" en memoria                                                                | `matricula.py`, `reportes.py` |
| `re`          | Expresiones regulares                                                                                            | `matricula.py`                  |
| `abc`         | `ABC` y `abstractmethod`: clases abstractas                                                                  | `reportes.py`                   |
| `tempfile`    | Carpeta temporal para la BD de pruebas                                                                           | `conftest.py`                   |
| `sqlite3`     | (indirecto) El "driver" que SQLAlchemy usa para hablar con SQLite                                                | —                                |

## 6.2 Dependencias de la aplicación (`dependencies` en `pyproject.toml`)

| Paquete                                      | Qué es                                                                                                                                                                                                          | Qué usamos de él                                                                                                                                                                                                                                         |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **fastapi**                            | Framework web para APIs                                                                                                                                                                                          | `FastAPI`, `APIRouter`, `Depends`, `HTTPException`, `status`, `Query`, `File`, `UploadFile`, `Response`, `FileResponse`, `StaticFiles`, `HTTPBearer`, `TestClient`                                                               |
| **starlette** *(la instala FastAPI)* | La base HTTP sobre la que corre FastAPI                                                                                                                                                                          | Indirectamente: rutas, respuestas, archivos estáticos                                                                                                                                                                                                     |
| **pydantic** *(la instala FastAPI)*  | Validación de datos con tipos                                                                                                                                                                                   | `BaseModel`, `Field`, `ConfigDict`                                                                                                                                                                                                                   |
| **uvicorn[standard]**                  | **Servidor ASGI**: el programa que escucha en el puerto 8000 y le pasa las peticiones a FastAPI                                                                                                            | Se ejecuta por consola: `uvicorn app.main:app`                                                                                                                                                                                                           |
| ↳ extras de `[standard]`                  | `uvloop` (bucle de eventos rápido, solo Linux/Mac), `httptools` (lector HTTP rápido), `watchfiles` (para `--reload`), `websockets`, `python-dotenv`, `pyyaml`, `colorama` (colores en Windows) | Automático                                                                                                                                                                                                                                                |
| **sqlalchemy**                         | ORM y constructor de consultas SQL                                                                                                                                                                               | `create_engine`, `event`, `sessionmaker`, `DeclarativeBase`, `Mapped`, `mapped_column`, `relationship`, `select`, `update`, tipos `String`, `Date`, `DateTime`, `Enum`, `ForeignKey`, `UniqueConstraint`, `IntegrityError` |
| **pyjwt**                              | Crear y verificar JSON Web Tokens                                                                                                                                                                                | `jwt.encode`, `jwt.decode`, `jwt.PyJWTError`                                                                                                                                                                                                         |
| **python-multipart**                   | Permite a FastAPI leer **formularios con archivos** (`multipart/form-data`). Sin ella, `UploadFile` no funciona                                                                                        | Indirecto (carga de matrícula)                                                                                                                                                                                                                            |
| **openpyxl**                           | Leer y escribir Excel `.xlsx`                                                                                                                                                                                  | `load_workbook`, `Workbook`, `Font`, `PatternFill`                                                                                                                                                                                                 |
| **fpdf2**                              | Generar PDF (se importa como `fpdf`)                                                                                                                                                                           | `FPDF`                                                                                                                                                                                                                                                   |
| ↳ `pillow`, `fonttools`                 | Imágenes y fuentes que usa fpdf2                                                                                                                                                                                | Indirecto                                                                                                                                                                                                                                                  |
| **tzdata**                             | Base de datos de zonas horarias. Linux la trae; **Windows y la imagen `python:slim` no**. Sin ella, `ZoneInfo("America/Caracas")` falla                                                                | Indirecto                                                                                                                                                                                                                                                  |

> **¿Qué es ASGI?** *Asynchronous Server Gateway Interface*: el estándar con el que un servidor (uvicorn) y un framework (FastAPI) se comunican. Gracias a ese estándar se pueden intercambiar: podríamos usar otro servidor ASGI sin tocar la app. Su antecesor síncrono, que usa Flask, es WSGI.

## 6.3 Dependencias de desarrollo (`[dependency-groups] dev`)

| Paquete                                                   | Para qué                                                                                                       |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **pytest**                                          | Framework de pruebas: descubre y ejecuta los tests, muestra resultados, maneja fixtures                         |
| **httpx**                                           | Cliente HTTP. `TestClient` de FastAPI lo usa por debajo para simular peticiones sin levantar un servidor real |
| ↳ `iniconfig`, `pluggy`, `pygments`, `packaging` | Dependencias internas de pytest                                                                                 |

> Al correr los tests aparece un aviso (*warning*) de Starlette que dice que usar `httpx` con su `TestClient` está obsoleto y sugiere otro paquete. **No es un error**: las 10 pruebas pasan. Es un aviso de que en una versión futura habrá que cambiar esa dependencia de desarrollo.

## 6.4 Herramientas fuera de Python

| Herramienta                                 | Para qué                                                           |
| ------------------------------------------- | ------------------------------------------------------------------- |
| **uv**                                | Gestor de proyecto, entornos virtuales y dependencias (Parte 3)     |
| **Docker** / **Docker Compose** | Empaquetar y desplegar (Parte 8)                                    |
| **Node.js + npm**                     | Solo para compilar el frontend (en la etapa 1 del Dockerfile)       |
| **git**                               | Control de versiones                                                |
| **Caddy** (recomendado)               | *Reverse proxy* con HTTPS automático delante de la app en el VPS |

---

# Parte 7 — Pruebas (tests)

## 7.1 ¿Qué es un test y por qué importa?

Un **test automatizado** es código que **ejecuta tu código y verifica que dé el resultado esperado**. Hasta ahora ustedes prueban así: corren el programa, escriben datos con `input()` y miran si el `print()` sale bien. Eso es una **prueba manual**. Funciona con un programa de 40 líneas. Con 1 500 líneas y 30 rutas, cada cambio podría romper algo en otra parte sin que nadie lo note.

Los tests automatizados:

1. **Detectan regresiones**: si mañana alguien cambia el algoritmo del QR y rompe la tolerancia de 30 s, el test falla en segundos.
2. **Son documentación ejecutable**: `test_flujo.py` cuenta, paso a paso, cómo se usa el sistema, y **no puede quedar desactualizado** porque si quedara, fallaría.
3. **Dan confianza para cambiar**: se puede refactorizar sabiendo que si los tests pasan, el comportamiento se mantiene.
4. **Obligan a buen diseño**: código difícil de probar suele ser código mal separado. Por eso los `services` no dependen de HTTP.

Correrlos:

```bash
cd backend && uv run pytest
```

Resultado actual:

```text
..........                                    [100%]
10 passed, 1 warning in 6.78s
```

Cada `.` es una prueba que pasó; una `F` sería una que falló, con el detalle de qué valor se esperaba y cuál llegó.

## 7.2 Tipos de pruebas: la pirámide

```text
            ▲  pocas, lentas, prueban TODO junto
           ╱ ╲
          ╱E2E╲          test_flujo.py: crear docente → sección → matrícula → clase → QR → marcar → estadísticas → PDF
         ╱─────╲
        ╱ Integ.╲        test_usuarios.py: varias piezas juntas (rutas + BD + seguridad)
       ╱─────────╲
      ╱ Unitarias ╲      test_servicios.py: una función/clase aislada, sin BD ni HTTP
     ╱─────────────╲
    ▼  muchas, rapidísimas
```

- **Unitaria** (*unit test*): prueba **una unidad** pequeña (una función, una clase) **aislada**. Ej.: `GeneradorCodigoQR` con instantes fijos. No hay servidor, ni red, ni base de datos. Tarda milisegundos.
- **De integración**: prueba que **varias piezas funcionen juntas** (ruta + dependencias + base de datos).
- **De punta a punta** (*end-to-end*, E2E): recorre un **caso de uso completo** como lo haría un usuario.

## 7.3 Cómo funciona pytest

- Busca archivos `test_*.py` dentro de `tests/` (lo configuramos en `pyproject.toml`).
- Dentro, ejecuta cada función que empiece con `test_`.
- Usa el **`assert`** normal de Python: `assert condicion`. Si la condición es falsa, la prueba falla y pytest muestra los valores.

```python
assert r.status_code == 201
assert r.json() == {"agregados": 4, "ya_inscritos": 0, "errores": []}
assert r.status_code == 200, r.text    # el segundo valor es el mensaje si falla
```

### Patrón AAA (Arrange – Act – Assert)

Casi todo test tiene tres partes: **preparar**, **actuar**, **verificar**.

```python
def test_codigo_qr_rota_y_tolera_ventana_anterior():
    g = GeneradorCodigoQR(ventana_segundos=30)       # ARRANGE: preparar
    t = 1_000_000.0
    codigo = g.generar("secreto", 1, instante=t)     # ACT: actuar
    assert g.es_valido("secreto", 1, codigo, instante=t)           # ASSERT: verificar
    assert g.es_valido("secreto", 1, codigo, instante=t + 30)      # ventana siguiente: aún vale
    assert not g.es_valido("secreto", 1, codigo, instante=t + 60)  # dos ventanas después: expiró
    assert not g.es_valido("otro", 1, codigo, instante=t)          # otro secreto
    assert not g.es_valido("secreto", 2, codigo, instante=t)       # otra clase
```

Fíjense en el **diseño para la prueba**: como `generar` y `es_valido` aceptan un `instante` opcional, podemos "viajar en el tiempo" sin esperar 60 segundos reales. Una prueba **determinista** da siempre el mismo resultado.

## 7.4 Fixtures y `conftest.py`

Una **fixture** es un recurso que varias pruebas necesitan (un cliente HTTP, un usuario logueado). Se declara una vez y pytest **lo inyecta** en cada test que lo pida **por el nombre del parámetro** (la misma idea que `Depends` en FastAPI).

```python
"""Configura una base de datos temporal ANTES de importar la app."""
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["STATIC_DIR"] = os.path.join(_tmp, "no-static")

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:   # el "with" ejecuta el lifespan (crea tablas y coordinador)
        yield c

@pytest.fixture(scope="session")
def token_coord(client):
    r = client.post("/api/auth/login", json={"usuario": "coordinador", "clave": "coordinador123"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}
```

Puntos clave:

1. **`conftest.py`** es un nombre especial: pytest lo carga **antes** que los tests, y sus fixtures están disponibles para todos.
2. **Base de datos temporal**: `tempfile.mkdtemp()` crea una carpeta vacía en el sistema. Las pruebas **nunca tocan** la base real.
3. **¿Por qué las variables de entorno van antes del `import`?** Porque `Settings` lee `os.getenv` **en el momento en que se importa** `config.py` (Parte 4.2). Si importáramos la app primero, ya habría leído la BD real. Por eso los imports están "fuera de lugar" y llevan `# noqa: E402`.
4. **`TestClient`** simula peticiones HTTP **sin levantar un servidor ni usar la red**: `client.post("/api/...", json={...})` devuelve una respuesta igual a la real.
5. **`scope="session"`**: la fixture se crea **una vez** para toda la corrida (no una vez por test). Más rápido, pero **todas las pruebas comparten la misma base de datos**. Por eso cada prueba usa nombres distintos (`prof`, `doc_clave`, `olvido`, `temporal`, `intento`, `nuevo_doc`) y códigos de sección distintos (`PROG3-A`, `TMP1`, `ED-1`), para no chocar entre sí.
6. **`token_coord(client)`**: una fixture que **depende de otra**. Hace login y devuelve la cabecera lista para usar.

## 7.5 Qué verifica cada prueba

### `test_servicios.py` — unitarias (lógica pura)

| Test                                              | Verifica                                                                                                                                                                                                                                                              |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_codigo_qr_rota_y_tolera_ventana_anterior` | El código vale en su ventana y en la siguiente, expira a la segunda, y no sirve con otro secreto ni para otra clase                                                                                                                                                  |
| `test_lector_csv_normaliza_y_deduplica`         | Con `;` como separador y encabezado "Cédula" con acento: `V-12.345.678` → `12345678`; la cédula repetida se queda con la **última** aparición (`ANA` → `Ana`); la fila vacía `;;` se ignora; la fila `x;;1` da "Fila 6: datos incompletos" |
| `test_lector_detecta_columnas_faltantes`        | Si falta una columna, no se procesa nada y se informa                                                                                                                                                                                                                 |

### `test_flujo.py` — punta a punta

Lee como una historia: crea docente y sección (verifica que `prog3-a` se guarde como `PROG3-A`) → carga 4 alumnos por CSV → el docente inicia sesión y **solo ve su sección** → abre clase → obtiene el código del QR → tres alumnos marcan (uno escribe `V-222`, que se normaliza) → marcar dos veces responde "Ya tenías…" → cédula no inscrita da **404** → código falso da **400** → segunda clase, se cierra y ya **no acepta** marcajes (400) → estadísticas: **50 %**, 100 % para 111, 3 en riesgo → panel general del coordinador; el docente recibe **403** → el PDF empieza con `%PDF` y el Excel con `PK` (un `.xlsx` es un ZIP por dentro, y los ZIP empiezan con `PK`) → pase de lista manual.

`test_sin_token_no_hay_acceso`: sin token → **401**.

### `test_usuarios.py` — gestión de usuarios y reglas

| Test                                               | Verifica                                                                                                                                                              |
| -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_cambiar_mi_clave`                          | Con clave actual incorrecta → 400; con la correcta → 204; la clave vieja deja de funcionar y la nueva sí                                                           |
| `test_coordinador_reinicia_clave_y_edita_nombre` | Editar sin clave no la cambia; editar con clave la reinicia                                                                                                           |
| `test_eliminar_docente_deja_seccion_sin_asignar` | Al borrar el docente, la sección sigue existiendo con `docente: null`                                                                                              |
| `test_alcance_solo_docentes`                     | Aunque se envíe `"rol": "coordinador"`, se crea docente; las rutas de docentes no editan ni borran al coordinador (404); un docente no puede listar docentes (403) |
| `test_editar_seccion_conserva_asistencias`       | La fecha de la clase sale de `hoy()` (zona horaria); cambiar código y docente conserva las clases; el nuevo docente ve la sección                                 |

## 7.6 Cómo escribir un test nuevo (receta)

1. Decidan **qué comportamiento** quieren garantizar, en una frase: *"un docente no puede borrar una sección"*.
2. Creen la función `test_...` en el archivo adecuado y pidan las fixtures que necesiten:

```python
def test_docente_no_puede_borrar_seccion(client, token_coord):
    # Arrange
    d = client.post("/api/docentes", headers=token_coord,
                    json={"usuario": "borrador", "nombre": "Prof Borrador", "clave": "secreta1"}).json()
    s = client.post("/api/secciones", headers=token_coord,
                    json={"codigo": "BOR-1", "asignatura": "Física", "docente_id": d["id"]}).json()
    r = client.post("/api/auth/login", json={"usuario": "borrador", "clave": "secreta1"})
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    # Act
    r = client.delete(f"/api/secciones/{s['id']}", headers=h)
    # Assert
    assert r.status_code == 403
```

3. Ejecuten `uv run pytest`. Si pasa, ¡listo! Si falla, o el test está mal o encontraron un bug.

---

# Parte 8 — Docker y despliegue

## 8.1 El problema: "en mi máquina sí funciona"

Para correr el proyecto en el VPS habría que instalar Python 3.12, uv, Node.js, compilar el frontend, configurar rutas… y rezar para que las versiones coincidan con las de tu laptop. **Docker** resuelve eso empaquetando la aplicación **con todo lo que necesita** (sistema base, Python, librerías, archivos) en una **imagen**.

## 8.2 Conceptos

| Concepto                   | Analogía                                 | Definición                                                                               |
| -------------------------- | ----------------------------------------- | ----------------------------------------------------------------------------------------- |
| **Imagen**           | La **receta** congelada, o un molde | Un paquete de solo lectura con sistema de archivos + programa + dependencias              |
| **Contenedor**       | El **pastel** hecho con el molde    | Una imagen **en ejecución**. Proceso aislado del resto del sistema                 |
| **Dockerfile**       | La receta escrita                         | Instrucciones para construir la imagen                                                    |
| **Capa** (*layer*) | Cada paso de la receta                    | Cada instrucción crea una capa; Docker **reutiliza** (cachea) las que no cambiaron |
| **Volumen**          | Un disco externo enchufado                | Carpeta que vive **fuera** del contenedor y sobrevive aunque el contenedor se borre |
| **Puerto**           | La puerta de la casa                      | Conecta un puerto del servidor con uno del contenedor                                     |
| **Docker Compose**   | El "control remoto"                       | Archivo YAML que describe cómo levantar los contenedores con un comando                  |

**Contenedor vs. máquina virtual:** una máquina virtual simula una computadora entera con su propio sistema operativo (pesada, minutos en arrancar). Un contenedor **comparte el núcleo** (*kernel*) del sistema anfitrión y solo aísla los procesos y archivos (liviano, segundos en arrancar).

## 8.3 El `Dockerfile`, línea por línea

Usamos una **construcción multi-etapa** (*multi-stage build*): una etapa para compilar el frontend con Node y otra final, solo con Python. Node **no** queda en la imagen final, que así es más pequeña y segura.

```dockerfile
# ---------- Etapa 1: frontend ----------
FROM node:22-alpine AS frontend
```

Parte de una imagen oficial con Node 22 sobre **Alpine** (una distribución Linux mínima, ~5 MB). `AS frontend` le pone nombre a la etapa.

```dockerfile
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
```

- `WORKDIR`: "entra" a esa carpeta (la crea si no existe).
- **Primero se copian solo los archivos de dependencias** y se instalan (`npm ci` = instalación limpia y exacta según el lock). **Después** se copia el resto del código. ¿Por qué en ese orden? Por la **caché de capas**: si solo cambias un componente de React, Docker reutiliza la capa de `npm ci` (que tarda) y solo repite el `build`.
- `npm run build` genera `/frontend/dist` (HTML, JS y CSS optimizados).

```dockerfile
# ---------- Etapa 2: backend ----------
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /usr/local/bin/uv
```

- `python:3.12-slim`: imagen oficial de Python, versión reducida (Debian).
- `COPY --from=<imagen>`: copia **el ejecutable `uv`** directamente desde la imagen oficial de uv, con **versión fija** (`0.11.29`) para reproducibilidad.

```dockerfile
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/app/.venv
```

- `UV_COMPILE_BYTECODE=1`: precompila los `.py` a `.pyc` durante la construcción → el contenedor arranca más rápido.
- `UV_LINK_MODE=copy`: copia los archivos en lugar de crear enlaces (los enlaces no funcionan bien entre capas de Docker).
- `UV_PROJECT_ENVIRONMENT=/app/.venv`: dónde crear el entorno virtual.

```dockerfile
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
```

El mismo truco de caché: **primero dependencias**, luego código.

- `--frozen`: usa `uv.lock` **tal cual**; si no coincide con `pyproject.toml`, falla en vez de actualizarlo. Producción = exactamente lo probado.
- `--no-dev`: **no** instala pytest ni httpx. En producción no hacen falta.
- `--no-install-project`: instala solo las dependencias, no el proyecto en sí (todavía no copiamos el código).

```dockerfile
COPY backend/app ./app
COPY --from=frontend /frontend/dist ./static
```

Copia el código del backend y **trae el frontend compilado desde la etapa 1** a `/app/static`.

```dockerfile
ENV PATH="/app/.venv/bin:$PATH" \
    STATIC_DIR=/app/static \
    DATABASE_URL=sqlite:////app/data/asistencia.db
```

- Antepone el `.venv` al `PATH` para que `uvicorn` sea el del entorno virtual.
- `sqlite:////app/data/...` con **cuatro barras**: `sqlite:///` es el prefijo y la cuarta `/` es el inicio de la **ruta absoluta** `/app/data/asistencia.db`.
- La `\` al final de línea continúa la instrucción en la siguiente.

```dockerfile
VOLUME /app/data
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
```

- `VOLUME /app/data`: la base de datos vive en un volumen, **fuera** de la imagen.
- `EXPOSE 8000`: documenta que la app escucha en el 8000.
- `CMD`: el comando que se ejecuta al arrancar el contenedor (formato lista = forma *exec*, sin pasar por un shell).
  - `--host 0.0.0.0`: escuchar en **todas** las interfaces. Con `127.0.0.1` (el valor por defecto) solo se podría acceder desde **dentro** del contenedor.
  - `--proxy-headers --forwarded-allow-ips=*`: confiar en las cabeceras `X-Forwarded-For` / `X-Forwarded-Proto` que pone el proxy (Caddy), para que la app sepa la IP real del cliente y que la conexión original era HTTPS.

## 8.4 `.dockerignore`

```text
**/node_modules
**/.venv
**/__pycache__
**/.pytest_cache
frontend/dist
backend/data
backend/static
backend/tests
.env
.git
```

Lo que **no** se envía a Docker al construir. Más rápido y más seguro: el `.env` con secretos **nunca** queda dentro de la imagen, ni la base de datos de tu laptop, ni los tests.

## 8.5 `docker-compose.yml`

```yaml
services:
  app:
    build: .                 # construye con el Dockerfile de esta carpeta
    ports:
      - "8000:8000"          # puerto_del_VPS:puerto_del_contenedor
    env_file: .env           # inyecta SECRET_KEY, ADMIN_CLAVE, etc. como variables de entorno
    volumes:
      - datos:/app/data      # volumen con nombre "datos" montado donde vive la BD
    restart: unless-stopped  # si se cae o el VPS se reinicia, vuelve a arrancar solo

volumes:
  datos:                     # declara el volumen; Docker lo gestiona
```

## 8.6 Desplegar en un VPS, paso a paso

```bash
git clone <url-del-repo> && cd asistencia-qr
```

```bash
cp .env.example .env
```

Editar `.env` (sobre todo `SECRET_KEY` con algo largo y aleatorio, y `ADMIN_CLAVE`). Para generar una buena clave:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

```bash
docker compose up -d --build
```

`-d` = en segundo plano (*detached*); `--build` = reconstruir la imagen. Para actualizar a una nueva versión: `git pull` y el mismo comando. La base de datos **sobrevive** porque está en el volumen.

**HTTPS:** las cámaras de los teléfonos y los navegadores modernos esperan HTTPS. Se pone **Caddy** delante como *reverse proxy* (proxy inverso: recibe las peticiones de Internet en el puerto 443 y se las pasa a la app en el 8000), y Caddy obtiene el certificado de **Let's Encrypt** automáticamente:

```text
asistencia.midominio.com {
    reverse_proxy localhost:8000
}
```

```text
Internet ──HTTPS:443──► Caddy ──HTTP:8000──► contenedor (uvicorn + FastAPI) ──► volumen "datos" (SQLite)
```

**Respaldo de la base de datos:**

```bash
docker compose cp app:/app/data/asistencia.db ./respaldo.db
```

---

# Parte 9 — Una petición de principio a fin

Seguimos a **Ana** marcando su asistencia. Esta sección une todo lo anterior.

```mermaid
sequenceDiagram
    participant P as Proyector (docente)
    participant T as Teléfono de Ana
    participant U as Uvicorn
    participant F as FastAPI (router)
    participant S as services
    participant D as SQLite

    P->>U: GET /api/clases/15/qr  (Bearer token, cada 2 s)
    U->>F: qr_actual()
    F->>S: generador_qr.generar(secreto, 15)
    S-->>F: "a3f91c07"
    F-->>P: {codigo, segundos_restantes: 18, presentes: 0, inscritos: 38}
    Note over P: Dibuja QR de https://.../asistir/15?c=a3f91c07
    T->>U: GET /api/publico/clases/15?c=a3f91c07
    U->>F: info_publica()
    F-->>T: {seccion: "PROG3-A", ..., codigo_valido: true}
    T->>U: POST /api/publico/asistencia {clase_id:15, codigo, cedula:"V-28.123.456"}
    U->>F: Pydantic valida MarcarIn
    F->>D: SELECT clase 15
    F->>S: es_valido(secreto, 15, codigo)
    F->>S: normalizar_cedula → "28123456"
    F->>D: SELECT estudiante JOIN inscripcion
    F->>D: INSERT asistencia + COMMIT
    D-->>F: OK (o IntegrityError si ya existía)
    F-->>T: 200 {"mensaje": "¡Asistencia registrada!", "estudiante": "Pérez Rodríguez, Ana María"}
    P->>U: GET /api/clases/15/qr
    F-->>P: {..., presentes: 1}
```

Con palabras, lo que pasa dentro del servidor en el `POST`:

1. **Uvicorn** recibe los bytes por la red, los interpreta como petición HTTP y se la entrega a FastAPI (por ASGI).
2. **FastAPI** busca la ruta: método `POST` + `/api/publico/asistencia` → función `marcar`.
3. Resuelve las **dependencias**: llama a `get_db()`, que abre una sesión y la pausa en el `yield`.
4. **Pydantic** convierte el JSON en un objeto `MarcarIn` y valida: `clase_id` entero, `cedula` de 1 a 20 caracteres. Si algo falla → 422 y fin.
5. Se ejecuta `marcar(datos, db)`: las 4 verificaciones (Parte 4.12).
6. `db.commit()` escribe en el archivo `asistencia.db`.
7. La función devuelve un `MarcarOut`; FastAPI lo valida con `response_model` y lo convierte a JSON.
8. Se reanuda `get_db()` después del `yield` y el `finally` **cierra la sesión**.
9. Uvicorn envía la respuesta `200 OK` al teléfono.

Todo esto ocurre en unos pocos milisegundos, y puede ocurrir para 40 teléfonos a la vez.

---

# Parte 10 — Prácticas profesionales y limitaciones honestas

## 10.1 Lo que hace "profesional" a este backend

| Práctica                                                                                             | Dónde se ve                                    |
| ----------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| **Separación en capas** (routers / services / models / schemas)                                | Toda la estructura de `app/`                  |
| **Configuración por entorno, sin secretos en el código**                                      | `config.py`, `.env.example`, `.gitignore` |
| **Validación declarativa de entradas**                                                         | `schemas.py` (Pydantic)                       |
| **DTOs separados de entidades**: nunca se filtra `clave_hash` ni `secreto`                  | `schemas.py` vs `models.py`                 |
| **Contraseñas con hash lento + sal**, comparación en tiempo constante                         | `security.py`                                 |
| **Autenticación sin estado (JWT)** con expiración                                             | `security.py`                                 |
| **Autorización declarativa** con dependencias; 404 para no revelar recursos ajenos (anti-IDOR) | `Depends(...)`, `obtener_seccion`           |
| **Integridad en la base de datos** (FK activadas, UNIQUE compuestos, cascadas)                  | `models.py`, `database.py`                  |
| **Transacciones**: o se guarda todo o nada                                                      | `commit()` único, `rollback()`             |
| **Evitar N+1**: consultas en lote, diccionarios y conjuntos                                     | `estadisticas.py`, `cargar_matricula`       |
| **Algoritmos con complejidad conocida** y documentada                                           | docstrings de `services/`                     |
| **POO con propósito**: herencia, polimorfismo, encapsulamiento, clases abstractas              | `reportes.py`, `models.py`                  |
| **Tests automatizados** en varios niveles, con BD temporal                                      | `tests/`                                      |
| **Builds reproducibles** (lock de dependencias, versiones fijas en Docker)                      | `uv.lock`, `Dockerfile`                     |
| **Imagen multi-etapa** pequeña y sin herramientas de desarrollo                                | `Dockerfile`                                  |
| **Persistencia en volumen**, reinicio automático                                               | `docker-compose.yml`                          |
| **Health check**                                                                                | `/api/salud`                                  |
| **Documentación automática de la API**                                                        | `/docs`                                       |
| **Protección de path traversal** al servir archivos                                            | `main.py`                                     |
| **Manejo de zona horaria** explícito                                                           | `config.hoy()`                                |
| **Código documentado** (docstrings explicando el *por qué*, no solo el *qué*)            | todos los archivos                              |

## 10.2 Limitaciones que conocemos (y por qué las aceptamos)

Mostrar que conocen los límites del sistema es lo que más convence de que lo dominan.

1. **Se puede reenviar el enlace dentro del minuto.** Un alumno en el aula puede escanear y mandar el enlace a un amigo, que tiene hasta ~60 s para usarlo. **Mitigación posible:** cuentas para alumnos, geolocalización, o vincular el marcaje al dispositivo. Fuera de alcance del MVP; el docente puede corregir con la lista manual.
2. **Alguien puede marcar con la cédula de otro** si tiene un código vigente. Misma mitigación que arriba.
3. **Sin límite de intentos** (*rate limiting*) en el login ni en el marcaje. En producción real se agregaría (por ejemplo, en el proxy).
4. **El token se guarda en `localStorage`** del navegador. Es lo más simple; una alternativa más robusta contra XSS son las *cookies* `HttpOnly`.
5. **Sin migraciones (Alembic)**: si cambia el esquema con datos ya en producción, habría que migrar a mano o adoptar Alembic.
6. **SQLite** escribe de a una transacción a la vez. Para una universidad sobra; con miles de escrituras por segundo se cambiaría a PostgreSQL (solo cambiando `DATABASE_URL`).
7. **Polling cada 2 s** en vez de WebSockets: más peticiones, pero muchísimo más simple, y para un aula es insignificante.
8. Los detalles finos ya mencionados: `PUT` que alterna (no idempotente), consultas síncronas dentro de una ruta `async`, y el promedio general calculado a partir de promedios redondeados.

---

# Parte 11 — Preguntas que puede hacer la profesora

**¿Por qué FastAPI y no Flask o Django?**
Django trae mucho más de lo que necesitamos (plantillas, panel de administración, su propio ORM) y está pensado para MVC con HTML generado en el servidor. Flask es mínimo pero habría que validar el JSON y documentar la API a mano. FastAPI valida con Pydantic, documenta sola en `/docs` y usa los type hints que ya escribimos. Para una API JSON consumida por React es lo más directo.

**¿Esto es MVC?**
Es una arquitectura en capas inspirada en MVC: los *routers* son controladores, `models.py` + `services/` son el modelo y la lógica de negocio, y la vista es React (en el backend, la "representación" la definen los `schemas`). Ver 2.8.

**¿Qué es una API REST? ¿Es REST la suya?**
Un estilo de API donde todo es un recurso con URL, el método HTTP indica la acción, cada petición es independiente (sin estado) y los códigos de estado tienen significado. Sí, con decisiones pragmáticas documentadas (`/cerrar`, `/reabrir`, el `PUT` que alterna).

**¿Cómo evitan que se marque asistencia desde la casa con una foto del QR?**
El QR cambia cada 30 segundos. El código es un HMAC-SHA256 del número de clase y de la "ventana de tiempo", firmado con un secreto único por clase que nunca sale del servidor. Solo se aceptan la ventana actual y la anterior, así que un código vale entre 30 y 60 segundos. Es el mismo principio que TOTP (Google Authenticator).

**¿Dónde guardan los códigos del QR?**
En ninguna parte. El servidor los recalcula al verificar. O(1), sin tablas ni limpieza.

**¿Cómo guardan las contraseñas?**
No las guardamos: guardamos un hash PBKDF2-SHA256 con sal aleatoria de 16 bytes y 200 000 iteraciones, en formato `sal$hash`. Para verificar recalculamos y comparamos con `hmac.compare_digest` en tiempo constante.

**¿Qué es un JWT y por qué lo usan?**
Un token firmado que contiene el id del usuario, su rol y la fecha de expiración. El servidor no guarda sesiones (*stateless*): cualquier petición se autentica verificando la firma con `SECRET_KEY`. Si alguien altera el contenido, la firma deja de coincidir. Ojo: el contenido es legible, no cifrado, por eso no lleva datos sensibles.

**¿Qué pasa si dos peticiones del mismo alumno llegan al mismo tiempo?**
La restricción `UNIQUE(clase_id, estudiante_id)` de la base de datos impide el duplicado. La segunda inserción lanza `IntegrityError`, hacemos `rollback()` y respondemos "Ya tenías la asistencia registrada".

**¿Qué es un ORM y qué ventaja tiene?**
Mapea clases Python a tablas SQL. Escribimos POO en lugar de SQL a mano, estamos protegidos contra inyección SQL, y podemos cambiar de SQLite a PostgreSQL cambiando una variable.

**¿Qué es el problema N+1 y cómo lo evitaron?**
Hacer una consulta por cada elemento de una lista (1 para la lista + N para los detalles). En estadísticas traemos todos los pares `(clase, estudiante)` en una consulta y contamos con `Counter` en un recorrido: O(A + E + C). En la matrícula usamos `WHERE cedula IN (...)` y diccionarios.

**¿Qué estructuras de datos usaron y por qué?**
Diccionarios (`dict`, `Counter`) para búsquedas y conteos en O(1); conjuntos (`set`) para pertenencia en O(1); listas ordenadas con `sorted` (Timsort, O(n log n)); dataclasses para resultados; un diccionario de estrategias (`GENERADORES`) para el polimorfismo.

**¿Dónde está la POO?**
Modelos ORM (herencia de `Base`, propiedades calculadas como `nombre_completo`), clases de servicio (`GeneradorCodigoQR`, `LectorMatricula`, `CalculadoraEstadisticas`), la jerarquía abstracta `GeneradorReporte` → `GeneradorExcel` / `GeneradorPDF` (herencia + polimorfismo + abierto/cerrado), y el `Enum` con herencia múltiple `Rol(str, Enum)`.

**¿Por qué un docente recibe 404 y no 403 cuando pide una sección ajena?**
Para no revelar que la sección existe. Protege contra IDOR (cambiar el id en la URL).

**¿Qué diferencia hay entre una prueba unitaria y una de integración?**
La unitaria prueba una pieza aislada (el generador de QR con instantes fijos, sin BD ni HTTP). La de integración/E2E prueba piezas trabajando juntas (rutas + seguridad + BD), como `test_flujo.py`.

**¿Por qué los tests no dañan la base de datos real?**
`conftest.py` apunta `DATABASE_URL` a una carpeta temporal antes de importar la app.

**¿Para qué sirven venv y uv?**
venv aísla las librerías de cada proyecto. uv crea ese entorno, instala versiones exactas según `uv.lock` y ejecuta comandos dentro de él (`uv run`), con un solo comando: `uv sync`.

**¿Para qué Docker si ya tienen uv?**
uv resuelve las librerías de Python. Docker empaqueta *todo*: el sistema base, Python, el frontend compilado y el backend, para que en el VPS corra idéntico. Con `docker compose up -d --build` queda desplegado, con la BD en un volumen persistente.

**¿Por qué el Dockerfile tiene dos `FROM`?**
Es multi-etapa: la primera compila React con Node; la segunda solo tiene Python y recibe los archivos compilados. Node no queda en la imagen final.

**¿Por qué SQLite y no PostgreSQL?**
Un archivo, cero configuración, cero contenedores extra, y aguanta de sobra el volumen de un aula. Gracias al ORM, migrar es cambiar `DATABASE_URL`.

**¿Qué pasa si la clase es a las 9 p. m.?**
El servidor está en UTC, donde ya sería el día siguiente. Por eso la fecha de cada clase se calcula con `hoy()` en la zona `America/Caracas`.

**¿Usaron IA?**
Sí, como herramienta, igual que se usan la documentación o Stack Overflow. Lo que demuestra dominio es poder explicar cada decisión, sus alternativas y sus límites — que es exactamente lo que recoge esta guía.

---

# Glosario

| Término                             | Definición breve                                                                                                                                              |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **API**                        | Contrato que define cómo un programa le pide cosas a otro                                                                                                     |
| **ASGI**                       | Estándar de comunicación entre servidor (uvicorn) y framework (FastAPI), con soporte asíncrono                                                              |
| **Backend**                    | La parte del sistema que corre en el servidor: lógica, datos, seguridad                                                                                       |
| **Bearer token**               | Token que se envía en `Authorization: Bearer ...`; quien lo porta, es el usuario                                                                            |
| **Cascada**                    | Borrar automáticamente los registros "hijos" al borrar el "padre"                                                                                             |
| **Clave foránea (FK)**        | Columna que apunta al id de otra tabla                                                                                                                         |
| **Clave primaria (PK)**        | Columna que identifica de forma única cada fila                                                                                                               |
| **Commit / Rollback**          | Confirmar / deshacer los cambios de una transacción                                                                                                           |
| **Contenedor**                 | Imagen de Docker en ejecución, aislada                                                                                                                        |
| **CORS**                       | Regla del navegador que bloquea peticiones entre orígenes distintos (dominio/puerto). Al servir API y frontend desde el mismo origen, no hay que configurarlo |
| **CRUD**                       | Create, Read, Update, Delete                                                                                                                                   |
| **Dependencia (FastAPI)**      | Función que FastAPI ejecuta antes de la ruta y cuyo resultado inyecta (`Depends`)                                                                           |
| **DTO**                        | Objeto solo para transportar datos hacia/desde afuera (nuestros schemas)                                                                                       |
| **Endpoint / ruta**            | Combinación método + URL que atiende una función                                                                                                            |
| **Fixture**                    | Recurso preparado para las pruebas (pytest)                                                                                                                    |
| **Framework**                  | Esqueleto de aplicación que llama a tu código (tú llenas los huecos)                                                                                        |
| **Hash**                       | Huella de un solo sentido de un dato                                                                                                                           |
| **HMAC**                       | Hash combinado con una clave secreta; solo quien tiene la clave puede generarlo                                                                                |
| **HTTP / HTTPS**               | Protocolo de la web / su versión cifrada                                                                                                                      |
| **Idempotente**                | Repetir la operación deja el mismo resultado                                                                                                                  |
| **IDOR**                       | Acceder a datos ajenos cambiando un id en la URL                                                                                                               |
| **Índice**                    | Estructura que acelera búsquedas en una columna                                                                                                               |
| **Inyección SQL**             | Ataque que mete instrucciones SQL dentro de un dato                                                                                                            |
| **JSON**                       | Formato de texto para datos (como dicts y listas)                                                                                                              |
| **JWT**                        | Token firmado con datos del usuario y expiración                                                                                                              |
| **Lifespan**                   | Código que corre al arrancar y apagar la app                                                                                                                  |
| **Middleware / proxy inverso** | Programa intermedio que recibe peticiones y las reenvía (Caddy)                                                                                               |
| **Migración**                 | Script versionado que cambia el esquema de una BD existente (Alembic)                                                                                          |
| **MIME type**                  | Etiqueta del tipo de contenido (`application/pdf`)                                                                                                           |
| **Monolito**                   | Una sola aplicación desplegable                                                                                                                               |
| **MVP**                        | Producto mínimo viable                                                                                                                                        |
| **N+1**                        | Antipatrón de hacer una consulta por cada elemento                                                                                                            |
| **OpenAPI / Swagger**          | Estándar para describir APIs / página interactiva que lo muestra (`/docs`)                                                                                 |
| **ORM**                        | Mapeo entre clases y tablas                                                                                                                                    |
| **Path traversal**             | Ataque que usa `../` para leer archivos fuera de la carpeta permitida                                                                                        |
| **Polling**                    | Preguntar al servidor cada cierto tiempo si hay novedades                                                                                                      |
| **Pydantic**                   | Librería de validación de datos con tipos                                                                                                                    |
| **REST**                       | Estilo de diseño de APIs basado en recursos y métodos HTTP                                                                                                   |
| **Sal (salt)**                 | Valor aleatorio que se mezcla con la clave antes de hashearla                                                                                                  |
| **Sesión (SQLAlchemy)**       | "Conversación" con la BD donde se acumulan cambios hasta el commit                                                                                            |
| **SPA**                        | Aplicación de una sola página; el navegador cambia la vista sin recargar                                                                                     |
| **SQL**                        | Lenguaje de consultas para bases de datos relacionales                                                                                                         |
| **Stateless**                  | El servidor no recuerda nada entre peticiones                                                                                                                  |
| **TOTP**                       | Contraseña de un solo uso basada en el tiempo                                                                                                                 |
| **Transacción**               | Conjunto de cambios que se aplican todos o ninguno                                                                                                             |
| **Type hint**                  | Anotación del tipo esperado (`x: int`)                                                                                                                      |
| **UTC**                        | Hora universal coordinada, referencia mundial                                                                                                                  |
| **uv**                         | Gestor de proyectos y dependencias de Python                                                                                                                   |
| **venv**                       | Entorno virtual: carpeta con Python y librerías aisladas por proyecto                                                                                         |
| **Volumen (Docker)**           | Almacenamiento que sobrevive al contenedor                                                                                                                     |

---

# Ejercicios para el equipo

Ordenados de fácil a difícil. Cada uno se puede comprobar con `uv run pytest` o desde `/docs`.

1. **Explorar `/docs`.** Levanten el backend, entren a `http://localhost:8000/docs`, hagan login con el botón *Try it out*, copien el token, pulsen **Authorize** y creen una sección. Luego provoquen a propósito un **401**, un **403**, un **404**, un **409** y un **422**, y expliquen cada uno.
2. **Leer un test como historia.** Tomen `test_flujo.py` y escriban en lenguaje natural qué hace cada bloque. Comparen con la Parte 1.2.
3. **Cambiar una constante.** Cambien `UMBRAL_RIESGO` a `50.0` y corran los tests. ¿Cuál falla y por qué? (Pista: el alumno 222 tiene exactamente 50 %, y la condición es `p < UMBRAL_RIESGO`, con `<` y no `<=`.) Después prueben con `80.0`: ¿por qué ahí **no** falla nada? Luego devuélvanlo a 75.
4. **Escribir un test unitario.** Prueben `LectorMatricula.normalizar_cedula` con `"V-12.345.678"`, `12345678.0` (float) y `None`.
5. **Escribir un test de integración.** El de la Parte 7.6 (un docente no puede borrar una sección → 403).
6. **Añadir un campo a la respuesta.** Agreguen `total_inscritos: int` a la información pública de la clase. ¿Qué archivos tocan? (schemas → router.) ¿Por qué no tocan `models.py`?
7. **Polimorfismo.** Creen `GeneradorCSV(GeneradorReporte)` con el módulo `csv` y regístrenlo en `GENERADORES`. ¿Qué más hay que cambiar para que `?formato=csv` funcione? (Pista: el `pattern` del `Query`.) Observen que **la ruta no cambia**: ese es el punto. *(Es solo un ejercicio; no forma parte del alcance del MVP.)*
8. **Docker.** Construyan y levanten con `docker compose up -d --build`, creen datos, ejecuten `docker compose down` y vuelvan a levantar. ¿Siguen los datos? ¿Por qué? Ahora `docker compose down -v` (borra volúmenes) y repitan. ¿Qué pasó?
9. **Complejidad.** Expliquen por qué `asistentes()` en `routers/clases.py` sería O(n²) si `presentes` fuera una lista en vez de un conjunto.
10. **Seguridad.** Copien un token **de su entorno de desarrollo** (nunca uno de producción) del navegador y péguenlo en [jwt.io](https://jwt.io). ¿Qué pueden leer? Cambien el rol a `coordinador`, intenten usarlo contra `/api/docentes` y expliquen por qué falla.

---

> **Para cerrar:** si después de esta guía alguien del equipo puede explicar con sus palabras (1) por qué el QR rota, (2) qué hace `Depends`, (3) cómo un objeto `Seccion` se convierte en una fila y luego en JSON, y (4) por qué la restricción `UNIQUE` vale más que un `if`, entonces domina este backend.
