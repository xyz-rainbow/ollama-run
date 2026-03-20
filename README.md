# 🌈 Rainbow Ollama-Run

An advanced Ollama orchestrator with tools, skills, persistent history, visual themes, and real-time thinking display.

![Rainbow Ollama-Run](banner.svg)

---

## Features

- **Native thinking display** — Real-time thought blocks with `ON`, `FORCE`, or `OFF` modes, using Ollama's native thinking API
- **Integrated tools** — Web search (DuckDuckGo), shell execution (`!command`), Logseq, system status. Toggle with `/tools`
- **Skills** — Activatable AI roles (code review, translation, SQL, security…). Toggle with `/skills`
- **Search skills** — Find and install new skills from `/skills → [Search skills]`
- **Persistent history** — Auto-saved to `~/.ollama-run/sessions/`. Load with `/history`
- **Visual themes** — `default`, `matrix`, `dracula`, `amber`, `mono`. Change in `/settings → Theme`
- **Model search & pull** — `/search` with `→` to browse variants, or `ollama-run pull <model>`
- **Persistent config** — Model, theme, tools and skills remembered between sessions (`~/.ollama-run/config.json`)
- **Input history** — Navigate previous prompts with `↑`/`↓` in the chat input
- **Image support** — Drag & drop images for vision models

---

## Installation

### Linux

```bash
git clone https://github.com/xyz-rainbow/ollama-run
cd ollama-run
./install.sh
```

The installer automatically handles Ollama, Python dependencies, and PATH setup.
Supports: **Ubuntu/Debian**, **Fedora/RHEL**, **Arch Linux**, and any distro with `apt`, `dnf`, or `pacman`.

### macOS

```bash
git clone https://github.com/xyz-rainbow/ollama-run
cd ollama-run
./install.sh
```

Requires [Homebrew](https://brew.sh) or will use the official Ollama installer as fallback.

### Windows

```batch
git clone https://github.com/xyz-rainbow/ollama-run
cd ollama-run
install.bat
```

Requires Python 3.10+ with "Add Python to PATH" checked during installation.
Download Python: https://www.python.org/downloads/
Download Ollama: https://ollama.com/download/windows

### WSL (Windows Subsystem for Linux)

```bash
git clone https://github.com/xyz-rainbow/ollama-run
cd ollama-run
./install.sh
```

> **Recommended:** Install Ollama on the Windows host, not inside WSL.
> Ollama running on Windows is accessible from WSL automatically.

### Manual install (any platform)

```bash
pip install ollama duckduckgo-search psutil requests
pip install -e .
```

Then run:

```bash
ollama-run
```

---

## Chat Commands

| Command | Description |
|---|---|
| `/settings` | Model, thinking mode, theme, pull, search, saved chats |
| `/tools` | Toggle tools on/off |
| `/skills` | Toggle AI skills on/off |
| `/search` | Browse and pull models from Ollama library |
| `/pull <model>` | Download a model |
| `/history` | View and resume past conversations |
| `/exit` | Exit |
| `!command` | Execute a shell command — output visible to you and the model |

## Menu Navigation

| Key | Action |
|---|---|
| `↑` `↓` | Navigate |
| `Enter` | Select |
| `Space` | Toggle ON/OFF (tools / skills) |
| `→` | View model details / variants |
| `Del` | Delete entry (history / skills) |
| `ESC` | Back / Cancel |

---

## Data files

```
~/.ollama-run/
├── config.json          # Persistent config (model, theme, tools, skills)
├── input_history        # Chat input history
├── sessions/            # Saved conversations
└── skills_catalog.json  # Installed skills
```

---

## Español

**Rainbow Ollama-Run** es un orquestador avanzado para Ollama con interfaz de terminal, pensamiento en tiempo real, herramientas, skills y historial persistente.

### Instalación

**Linux / macOS / WSL:**

```bash
git clone https://github.com/xyz-rainbow/ollama-run
cd ollama-run
./install.sh
```

**Windows:**

```batch
git clone https://github.com/xyz-rainbow/ollama-run
cd ollama-run
install.bat
```

Requiere Python 3.10+ con "Add Python to PATH" marcado, y [Ollama para Windows](https://ollama.com/download/windows).

### Comandos principales

| Comando | Descripción |
|---|---|
| `/settings` | Modelo, pensamiento, tema, historial |
| `/tools` | Activar/desactivar herramientas |
| `/skills` | Activar/desactivar skills |
| `/search` | Buscar modelos en Ollama library |
| `/history` | Ver y cargar conversaciones anteriores |
| `!comando` | Ejecutar comando de shell |

---

## License

**© Rainbow Technology — Personal Use Only**

This software is licensed for **personal, non-commercial use only**.

- You may use, run, and modify this software for personal purposes.
- Pull requests and contributions are welcome.
- **You may NOT** sell, sublicense, or distribute this software or any derivative work.
- **Forks are not permitted** without explicit written authorization from Rainbow Technology.
- Any unauthorized modification, redistribution, or commercial use will be reported and pursued legally.

> *"Se permiten commits para aportar, pero no para vender o hacer forks. Cualquier uso no autorizado será denunciable."*

For permissions beyond personal use, contact: **#xyz-rainbow** | **rainbowtechnology.xyz**

---

#xyz-rainbow | #xyz-rainbowtechnology | #rainbowtechnology.xyz
