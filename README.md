# 🌈 Rainbow Ollama-Run

An advanced Ollama orchestrator with tools, skills, persistent history, visual themes, and real-time thinking display.

> Un orquestador avanzado para Ollama con herramientas, skills, historial persistente, temas visuales y visualización del pensamiento en tiempo real.

![Rainbow Ollama-Run](banner.svg)

---

## Features / Características

- **Native thinking display** — Real-time thought blocks with `ON`, `FORCE`, or `OFF` modes
- **Integrated tools** — Web search, shell execution (`!command`), Logseq, system status. Toggle with `/tools`
- **Skills** — Activatable AI roles (code review, translation, SQL, security…). Toggle with `/skills`
- **Search tools & skills** — Find and install new tools/skills from their menus
- **Persistent history** — Auto-saved to `~/.ollama-run/sessions/`. Load with `/history`
- **Visual themes** — `default`, `matrix`, `dracula`, `amber`, `mono`. Change in `/settings`
- **Model search & pull** — `/search` with `→` to browse variants, or `ollama-run pull <model>`
- **Input history** — Navigate previous prompts with `↑`/`↓` in chat
- **Image support** — Drag & drop images for vision models

---

- **Pensamiento en tiempo real** — Bloques de razonamiento con modos `ON`, `FORCE` u `OFF`
- **Herramientas integradas** — Búsqueda web, shell (`!comando`), Logseq, estado del sistema. Toggle con `/tools`
- **Skills** — Roles de IA activables (code review, traducción, SQL, seguridad…). Toggle con `/skills`
- **Buscar tools y skills** — Encuentra e instala nuevas tools/skills desde sus menús
- **Historial persistente** — Guardado automático en `~/.ollama-run/sessions/`. Cargar con `/history`
- **Temas visuales** — `default`, `matrix`, `dracula`, `amber`, `mono`. Cambia en `/settings`
- **Buscar y descargar modelos** — `/search` con `→` para ver variantes, o `ollama-run pull <modelo>`
- **Historial de entrada** — Navega prompts anteriores con `↑`/`↓` en el chat
- **Soporte de imágenes** — Arrastra imágenes para modelos de visión

---

## Installation / Instalación

### Linux

```bash
git clone https://github.com/xyz-rainbow/ollama-run
cd ollama-run
./install.sh
```

The installer automatically handles Ollama, Python dependencies, and PATH setup.
Supports: **Ubuntu/Debian**, **Fedora/RHEL**, **Arch Linux**, and any distro with `apt`, `dnf`, or `pacman`.

> El instalador gestiona automáticamente Ollama, dependencias Python y el PATH.
> Compatible con: **Ubuntu/Debian**, **Fedora/RHEL**, **Arch Linux** y cualquier distro con `apt`, `dnf` o `pacman`.

---

### macOS

```bash
git clone https://github.com/xyz-rainbow/ollama-run
cd ollama-run
./install.sh
```

Requires [Homebrew](https://brew.sh) or will use the official Ollama installer as fallback.

> Requiere [Homebrew](https://brew.sh) o usará el instalador oficial de Ollama como alternativa.

---

### Windows

```batch
git clone https://github.com/xyz-rainbow/ollama-run
cd ollama-run
install.bat
```

Requires Python 3.10+ with "Add Python to PATH" checked during installation.
Download Python: https://www.python.org/downloads/
Download Ollama: https://ollama.com/download/windows

> Requiere Python 3.10+ con "Add Python to PATH" marcado durante la instalación.
> Descarga Python: https://www.python.org/downloads/
> Descarga Ollama: https://ollama.com/download/windows

---

### WSL (Windows Subsystem for Linux)

```bash
git clone https://github.com/xyz-rainbow/ollama-run
cd ollama-run
./install.sh
```

**Recommended:** Install Ollama on the Windows host, not inside WSL. Ollama running on Windows is accessible from WSL automatically.

> **Recomendado:** Instala Ollama en Windows (host), no dentro de WSL. Ollama en Windows es accesible desde WSL automáticamente.

---

### Manual install / Instalación manual

```bash
pip install ollama duckduckgo-search psutil requests
pip install -e .
ollama-run
```

---

## Chat Commands / Comandos en el chat

| Command | Description | Comando | Descripción |
|---|---|---|---|
| `/settings` | Model, thinking, theme, history | `/settings` | Modelo, pensamiento, tema, historial |
| `/tools` | Toggle tools on/off | `/tools` | Activar/desactivar herramientas |
| `/skills` | Toggle AI skills on/off | `/skills` | Activar/desactivar skills |
| `/search` | Browse and pull models | `/search` | Buscar y descargar modelos |
| `/pull <model>` | Download a model | `/pull <modelo>` | Descargar un modelo |
| `/history` | View and resume past chats | `/history` | Ver y cargar conversaciones |
| `/exit` | Exit | `/exit` | Salir |
| `!command` | Run a shell command | `!comando` | Ejecutar comando de shell |

---

## Menu Navigation / Navegación en menús

| Key / Tecla | Action / Acción |
|---|---|
| `↑` `↓` | Navigate / Navegar |
| `Enter` | Select / Seleccionar |
| `Space` | Toggle ON/OFF (tools / skills) |
| `→` | Model details / Detalles del modelo |
| `Del` | Delete custom entry / Borrar entrada personalizada |
| `ESC` | Back / Volver |

---

## Data files / Archivos de datos

```
~/.ollama-run/
├── config.json          # Persistent config — Configuración persistente
├── input_history        # Chat input history — Historial de entrada
├── sessions/            # Saved conversations — Conversaciones guardadas
├── skills_catalog.json  # Installed skills — Skills instaladas
└── custom_tools.json    # Custom tools — Herramientas personalizadas
```

---

## License / Licencia

**© Rainbow Technology — Personal Use Only / Solo Uso Personal**

This software is licensed for **personal, non-commercial use only**.

- You may use, run, and modify this software for personal purposes.
- Pull requests and contributions are welcome.
- **You may NOT** sell, sublicense, or distribute this software or any derivative work.
- **Forks are not permitted** without explicit written authorization from Rainbow Technology.
- Any unauthorized modification, redistribution, or commercial use will be reported and pursued legally.

---

Este software está licenciado **exclusivamente para uso personal y no comercial**.

- Puedes usar, ejecutar y modificar este software para fines personales.
- Los pull requests y contribuciones son bienvenidos.
- **No está permitido** vender, sublicenciar ni distribuir este software ni ningún trabajo derivado.
- **No se permiten forks** sin autorización escrita explícita de Rainbow Technology.
- Cualquier modificación, redistribución o uso comercial no autorizado será denunciado y perseguido legalmente.

---

#xyz-rainbow | #xyz-rainbowtechnology | #rainbowtechnology.xyz
