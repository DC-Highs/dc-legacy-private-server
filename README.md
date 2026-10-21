<img width="330" height="230" alt="image" src="https://github.com/user-attachments/assets/1d1d8f52-cb5d-429e-bb72-e43ee86b1a44" />


**Dragon City Flash Restoration Project** — Un proyecto de preservación histórica del juego
original en Adobe Flash (2012–2020), mantenido vivo por la comunidad.

[![Estado](https://img.shields.io/badge/Estado-En_Desarrollo-orange)]()
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)]()
[![Flask](https://img.shields.io/badge/Flask-Servidor_Local-lightgrey)]()
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

El servidor local es funcional y permite cargar el juego.

| Módulo | Estado |
|---|---|
| Motor de Cría | ✅ Funcional |
| Comandos (`packet.php`) | ⚠️ 60 / 104 implementados |
| Minijuego: Reflejo del Dragón | ✅ Funcional |
| Minijuego: Memoria | ❌ En desarrollo |
| Minijuego: Tesoro | ❌ En desarrollo |

### 🎮 Sobre los Minijuegos

Los minijuegos incluidos en este proyecto **no forman parte del Dragon City original**.
Son creaciones propias desarrolladas para suplir una limitación técnica del entorno local:
dado que el sistema de compra de gemas no puede funcionar sin los servidores oficiales,
estos minijuegos ofrecen al jugador una forma alternativa de obtenerlas y disfrutar
del juego de manera completa.


---

## 🚀 Instalación

### Requisitos

- Un navegador moderno. El juego se ejecuta con [Ruffle](https://ruffle.rs/), que se carga
  desde `index.html`, así que ya no hace falta Flash Player (se necesita conexión a internet
  para descargarlo desde unpkg).
  - Alternativa: [FlashBrowser](https://github.com/radubirsan/FlashBrowser/releases/latest)
    o [Pale Moon](https://www.palemoon.org/) con Flash Player.
- Permisos de **administrador**: el servidor agrega entradas al archivo `hosts` de Windows
  (y las elimina al cerrarse) y escucha en el puerto 80.

### Opción A: ejecutable

1. Descarga la última versión desde la sección [Releases](../../releases/latest).
2. Extrae el archivo `.zip` en la carpeta que prefieras.
3. Ejecuta `Dragon City.exe` como administrador.

> ⚠️ **Nota:** Windows puede mostrar una advertencia de SmartScreen al ejecutar el archivo.
> Haz clic en **"Más información" → "Ejecutar de todas formas"**. Esto es normal en ejecutables
> que no están firmados digitalmente.

### Opción B: desde el código fuente

Requiere Python 3.9+ y [Poetry](https://python-poetry.org/).

```bash
poetry install
poetry run dragon-city      # ejecutar en una terminal con permisos de administrador
```

También funciona con `poetry run python -m dragon_city`. El nivel de logs se cambia con la
variable de entorno `DRAGON_CITY_LOG_LEVEL` (por defecto `INFO`).

Después abre el navegador en `http://127.0.0.1:80`.

---

## 🧱 Estructura del Proyecto

```
src/dragon_city/
├── __main__.py        # punto de entrada (hosts, servidor de políticas, Flask)
├── app.py             # fábrica de la aplicación Flask (CORS + blueprints)
├── enums.py           # comandos, eventos SSE, recursos, atributos...
├── config.py          # rutas y constantes
├── storage.py         # lectura/escritura de configuración y partidas (web/srv)
├── commands/          # un módulo por comando de packet.php
├── game/              # reglas: cría, mercado negro, mercado, PvP, dragonario...
└── routes/            # blueprints HTTP (páginas, srv, packet, mercado, minijuegos...)
```

Para agregar un comando, crea un módulo en `commands/` con un manejador decorado con
`@command(Command.X)` (y agrega el valor al enum `Command`).

---

## 🎮 Cómo Jugar

- Inicia el servidor y navega a `http://127.0.0.1:80` en tu navegador.
- Crea un perfil en la pantalla de inicio y disfruta.

---

## 💾 Guardado

El progreso se guarda localmente en archivos `.json` dentro de la carpeta `web/srv/`
Cuando crees un usuario, usá los botones Exportar / Importar que están en login.html para hacer copias de seguridad de tus usuarios (esto respalda los usuarios creados, no las partidas).

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
