#!/usr/bin/env bash
# Rainbow Ollama-Run — Installer (Linux / macOS / WSL)
# #xyz-rainbow #rainbowtechnology.xyz

set -e

CYAN='\033[1;96m'; GREEN='\033[1;32m'; YELLOW='\033[1;33m'
RED='\033[1;31m';  DIM='\033[2m';      RESET='\033[0m'

echo -e "\n  ${CYAN}[XYZ]${RESET} \033[1;37mOLLAMA-RUN${RESET} ${DIM}installer${RESET}\n"

# ── Detectar OS ────────────────────────────────────────────────────────────────
OS="linux"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
elif grep -qi microsoft /proc/version 2>/dev/null; then
    OS="wsl"
fi
echo -e "  ${DIM}Sistema detectado: $OS${RESET}"

# ── 1. Instalar Ollama ─────────────────────────────────────────────────────────
if command -v ollama &>/dev/null; then
    echo -e "  ${GREEN}✓ Ollama ya instalado: $(ollama --version 2>/dev/null | head -1)${RESET}"
else
    echo -e "  ${YELLOW}Ollama no encontrado. Instalando…${RESET}"
    if [[ "$OS" == "mac" ]]; then
        if command -v brew &>/dev/null; then
            brew install ollama
        else
            echo -e "  ${DIM}Homebrew no encontrado, usando instalador oficial…${RESET}"
            curl -fsSL https://ollama.com/install.sh | sh
        fi
    elif [[ "$OS" == "wsl" ]]; then
        echo -e "  ${YELLOW}En WSL se recomienda instalar Ollama en Windows.${RESET}"
        echo -e "  ${DIM}Descarga: https://ollama.com/download/windows${RESET}"
        echo -e "  ${DIM}Intentando instalación Linux de todas formas…${RESET}"
        curl -fsSL https://ollama.com/install.sh | sh || true
    else
        # Linux
        if command -v curl &>/dev/null; then
            curl -fsSL https://ollama.com/install.sh | sh
        elif command -v wget &>/dev/null; then
            wget -qO- https://ollama.com/install.sh | sh
        else
            echo -e "  ${RED}✗ Necesitas curl o wget.${RESET}"; exit 1
        fi
    fi
    echo -e "  ${GREEN}✓ Ollama instalado.${RESET}"
fi

# ── 2. Python y pip ────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo -e "  ${YELLOW}Python3 no encontrado. Instalando…${RESET}"
    if [[ "$OS" == "mac" ]]; then
        brew install python3
    elif command -v apt-get &>/dev/null; then
        sudo apt-get install -y python3 python3-pip
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3 python3-pip
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm python python-pip
    else
        echo -e "  ${RED}✗ Instala Python3 manualmente.${RESET}"; exit 1
    fi
fi

# ── 3. Dependencias Python ─────────────────────────────────────────────────────
echo -e "  ${DIM}Instalando dependencias Python…${RESET}"
pip3 install -r requirements.txt --break-system-packages -q 2>/dev/null \
    || pip3 install -r requirements.txt --user -q 2>/dev/null \
    || pip3 install -r requirements.txt -q

# ── 4. Instalar ollama-run ─────────────────────────────────────────────────────
echo -e "  ${DIM}Instalando ollama-run…${RESET}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pip3 install -e "$SCRIPT_DIR" --break-system-packages -q 2>/dev/null \
    || pip3 install -e "$SCRIPT_DIR" --user -q 2>/dev/null \
    || pip3 install -e "$SCRIPT_DIR" -q

# ── 5. PATH: ~/.local/bin ──────────────────────────────────────────────────────
LOCAL_BIN="$HOME/.local/bin"

# Detectar shell rc
detect_rc() {
    if [[ -n "$ZSH_VERSION" ]] || [[ "$(basename "$SHELL")" == "zsh" ]]; then
        echo "$HOME/.zshrc"
    elif [[ -n "$FISH_VERSION" ]] || [[ "$(basename "$SHELL")" == "fish" ]]; then
        echo "$HOME/.config/fish/config.fish"
    else
        echo "$HOME/.bashrc"
    fi
}
SHELL_RC=$(detect_rc)

# Añadir al PATH si no está
add_to_path() {
    local rc="$1"
    local bin="$2"
    if [[ -f "$rc" ]] && ! grep -q "$bin" "$rc" 2>/dev/null; then
        if [[ "$rc" == *"config.fish" ]]; then
            echo -e "\nset -gx PATH \$PATH $bin  # ollama-run" >> "$rc"
        else
            printf '\n# ollama-run\nexport PATH="$PATH:%s"\n' "$bin" >> "$rc"
        fi
        echo -e "  ${GREEN}✓ $bin añadido al PATH en $rc${RESET}"
    fi
}

mkdir -p "$LOCAL_BIN"
add_to_path "$SHELL_RC" "$LOCAL_BIN"

# macOS: también ~/.zprofile para terminales de login
if [[ "$OS" == "mac" ]] && [[ -f "$HOME/.zprofile" ]]; then
    add_to_path "$HOME/.zprofile" "$LOCAL_BIN"
fi

# Exportar para la sesión actual
export PATH="$PATH:$LOCAL_BIN"

# ── 6. Limpiar alias rotos previos ─────────────────────────────────────────────
for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_aliases"; do
    [[ -f "$rc" ]] && sed -i '/alias ollama-run=/d' "$rc" 2>/dev/null || true
done

# ── 7. Verificar ──────────────────────────────────────────────────────────────
echo ""
if command -v ollama-run &>/dev/null || [[ -f "$LOCAL_BIN/ollama-run" ]]; then
    echo -e "  ${GREEN}✓ Todo listo.${RESET}"
    echo -e "  ${DIM}Ejecuta:${RESET} ${CYAN}ollama-run${RESET}"
    echo -e "  ${DIM}(Si no responde aún: source $SHELL_RC)${RESET}\n"
else
    echo -e "  ${YELLOW}⚠ Instalado pero fuera del PATH actual.${RESET}"
    echo -e "  ${DIM}Ejecuta:${RESET}  source $SHELL_RC  ${DIM}y luego${RESET}  ollama-run\n"
fi
