<img width="330" height="230" alt="image" src="https://github.com/user-attachments/assets/1d1d8f52-cb5d-429e-bb72-e43ee86b1a44" />


**Dragon City Flash Restoration Project** — Un proyecto de preservación histórica del juego
original en Adobe Flash (2012–2020), mantenido vivo por la comunidad.

[![Estado](https://img.shields.io/badge/Estado-En_Desarrollo-orange)]()
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)]()
[![Flask](https://img.shields.io/badge/Flask-Servidor-lightgrey)]()
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)]()
[![Licencia](https://img.shields.io/badge/Licencia-MIT-green.svg)](LICENSE)
[![Comandos](https://img.shields.io/badge/Comandos_Implementados-60%2F104-yellow)]()

---

## ⚠️ Aviso Legal / Legal Notice

**Este proyecto es de uso estrictamente educativo y de preservación histórica.**
*Dragon City* y todos sus activos visuales, de audio y de marca son propiedad intelectual
de **SocialPoint / Take-Two Interactive**.

Este servidor local:
- **NO** tiene fines de lucro ni distribuye el juego comercialmente.
- **NO** compite con las versiones actuales del juego (móvil / Windows).
- Opera bajo el amparo de las exenciones a la **Sección 1201 de la DMCA**, relativas a la
  preservación de videojuegos cuyos servidores de autenticación originales han sido
  apagados de forma permanente.
- Utiliza protocolos y activos de la versión de **Adobe Flash**, plataforma
  oficialmente descontinuada desde diciembre de 2020.

Si eres representante legal de SocialPoint o Take-Two Interactive y tienes alguna consulta,
puedes contactarme antes de tomar cualquier acción formal.

---

## 🛠️ Estado del Desarrollo

El servidor es funcional: se juega en el navegador (Ruffle), con cuentas, y se despliega con Docker.

| Módulo | Estado |
|---|---|
| Motor de Cría | ✅ Funcional |
| Comandos (`packet.php`) | ⚠️ 60 / 104 implementados |
| Cuentas (registro, login, panel de admin) | ✅ Funcional |
| Guardado en MongoDB, cuentas en PostgreSQL | ✅ Funcional |
| Interfaz de minijuegos y mercado | ❌ Sin interfaz (la API sigue disponible) |

---

## 🚀 Instalación (Docker)

El servidor corre en contenedores: la aplicación, PostgreSQL (cuentas y sesiones) y MongoDB
(el estado de cada jugador). Sirve igual en tu PC con Docker Desktop que en una VPS.

### Requisitos

- Docker con Docker Compose.
- Los archivos del juego en `flash/`, `assets/` y `domains/` (no van dentro de la imagen: se
  montan como volúmenes de solo lectura).

### Pasos

```bash
cp .env.example .env        # y completa POSTGRES_PASSWORD, MONGO_PASSWORD y ADMIN_*
docker compose up -d --build
```

Abre `http://localhost:8080` (o el `APP_PORT` que elijas), crea una cuenta y juega. Con
`ADMIN_EMAIL` y `ADMIN_PASSWORD` se crea el primer administrador al iniciar; también puedes
crearlo después:

```bash
docker compose exec app python -m dragon_city create-admin --email tu@correo.com --password '...'
```

Las cuentas se registran con correo y contraseña (sin código de confirmación). Los
administradores gestionan usuarios en `/admin`: crear, buscar, deshabilitar, cambiar
contraseña, editar recursos, reiniciar la partida o borrar.

### En una VPS

- Los puertos de las bases de datos **no** se publican; solo la aplicación (`APP_PORT`).
- Pon un proxy con HTTPS delante (nginx, Traefik, Caddy...) y en `.env` usa
  `COOKIE_SECURE=true` y `TRUST_PROXY=true`. Sin HTTPS las contraseñas viajan sin cifrar.
- El proxy no debe almacenar en búfer `/stream` (eventos del servidor); la aplicación ya envía
  `X-Accel-Buffering: no`.
- La aplicación usa **un solo proceso** a propósito (notificaciones en vivo, bloqueos por
  jugador y límites de uso viven en memoria). No escales a varias réplicas.
- Respaldo: `docker compose exec postgres pg_dump -U dragon dragoncity > cuentas.sql` y
  `docker compose exec mongo mongodump -u dragon -p ... --authenticationDatabase admin --archive > partidas.archive`.

### Desarrollo

```bash
poetry install
cd frontend && npm install && npm run dev      # cliente web con recarga (proxy a :8080)
poetry run pytest                              # pruebas (SQLite + mongomock, sin Docker)
```

---

## 🎮 Cómo Jugar

- Abre el sitio, crea una cuenta o inicia sesión: el juego ocupa casi toda la pantalla, con un
  encabezado para iniciar/cerrar sesión.

---

## 🧱 Estructura del Proyecto

```
src/dragon_city/
├── cli.py, wsgi.py     # comandos (migrate, create-admin...) y entrada de gunicorn
├── app.py              # fábrica de Flask
├── config.py           # configuración por variables de entorno
├── db/                 # modelos SQLAlchemy (PostgreSQL) y acceso a MongoDB
├── auth/               # contraseñas (Argon2id), sesiones, protección CSRF
├── api/                # API JSON: auth, admin, arranque del juego
├── commands/           # un módulo por comando de packet.php + validación
├── game/               # reglas: cría, mercado negro, mercado, PvP, dragonario...
├── routes/             # endpoints del protocolo original y archivos del juego
└── migrations/         # migraciones de PostgreSQL (Alembic)
frontend/               # cliente web (Vite, React, shadcn/ui)
docs/SECURITY.md        # modelo de seguridad y vulnerabilidades corregidas
```

Para agregar un comando, crea un módulo en `commands/` con un manejador decorado con
`@command(Command.X)`, valida **todos** los argumentos con los helpers de `ctx` y agrega el
valor al enum `Command`. Lee `docs/SECURITY.md` antes.

---

## 💾 Guardado

El progreso de cada jugador se guarda en MongoDB (colección `players`); las cuentas y sesiones,
en PostgreSQL. Los archivos de `web/srv/` (configuración del juego, plantilla de jugador y
oponentes PvP) son datos de arranque de solo lectura.

---

## 📚 Sobre la Preservación del Patrimonio Digital

- [Exemption to PCCPSACT](https://www.federalregister.gov/documents/2018/10/26/2018-23241/exemption-to-prohibition-on-circumvention-of-copyright-protection-systems-for-access-control) — Exenciones a la Sección 1201 de la DMCA.
- [EFGAMP](https://efgamp.eu/) — Federación Europea de Archivos y Museos de Videojuegos.
- [BlueMaxima's Flashpoint](https://bluemaxima.org/flashpoint/) — Proyecto definitivo de preservación de juegos web.
- [The Internet Archive](https://archive.org/) — Biblioteca digital de artefactos culturales.
- [UNESCO PERSIST Programme](https://unescopersist.org/) — Acceso continuo a la información digital.
- [Adobe Flash Player Archive](https://archive.org/download/flashplayerarchive/) — Archivo histórico de Flash Player.

---

## 📄 Licencia

El código fuente del servidor (`src/`, y los `.html` adaptados) está bajo la
[Licencia MIT](LICENSE).

Los activos originales del juego (`.swf`, imágenes, audio) **no** están cubiertos por esa
licencia: pertenecen a SocialPoint / Take-Two Interactive.

Autores: [Gabriel18017](https://github.com/Gabriel18017) y [Marcuth](https://github.com/Marcuth).
