#!/usr/bin/env bash
# =============================================================================
# iniciar.sh — Paper.io 2: Edição Brasil
# -----------------------------------------------------------------------------
# Instala as dependências em um ambiente virtual Python isolado e inicia o jogo.
# Compatível com Ubuntu 20.04+ e derivados (Mint, Pop!_OS, etc.).
#
# Uso:
#   chmod +x iniciar.sh   # (apenas na primeira vez)
#   ./iniciar.sh
#
# O que este script faz:
#   1. Verifica Python 3.9+
#   2. Instala python3-venv se necessário (via apt)
#   3. Cria/reutiliza o ambiente virtual .venv/ na raiz do projeto
#   4. Instala pygame e numpy dentro do venv
#   5. Inicia o jogo
# =============================================================================

set -euo pipefail

# ── Cores para output ─────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'   # reset

# ── Diretório do script (funciona de qualquer CWD) ────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON_MIN_MAJOR=3
PYTHON_MIN_MINOR=9

echo ""
echo -e "${BOLD}${CYAN}  Paper.io 2 — Edição Brasil${NC}"
echo -e "${CYAN}  ────────────────────────────────────────${NC}"
echo ""

# ── 1. Localizar Python 3 ─────────────────────────────────────────────────────
find_python() {
    for cmd in python3.12 python3.11 python3.10 python3.9 python3; do
        if command -v "$cmd" &>/dev/null; then
            local ver
            ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
            local major minor
            major=$(echo "$ver" | cut -d. -f1)
            minor=$(echo "$ver" | cut -d. -f2)
            if [ "$major" -ge "$PYTHON_MIN_MAJOR" ] && [ "$minor" -ge "$PYTHON_MIN_MINOR" ]; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

PYTHON=""
if ! PYTHON=$(find_python); then
    echo -e "${RED}  ✗ Python $PYTHON_MIN_MAJOR.$PYTHON_MIN_MINOR+ não encontrado.${NC}"
    echo -e "${YELLOW}  → Instale com:  sudo apt install python3${NC}"
    exit 1
fi

PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
echo -e "  ${GREEN}✔${NC} Python ${BOLD}$PY_VER${NC} encontrado em $(command -v "$PYTHON")"

# ── 2. Garantir python3-venv ──────────────────────────────────────────────────
if ! "$PYTHON" -c "import venv" &>/dev/null; then
    echo -e "  ${YELLOW}→ Instalando python3-venv (requer sudo)...${NC}"
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y python3-venv python3-dev
    else
        echo -e "${RED}  ✗ apt-get não encontrado. Instale python3-venv manualmente.${NC}"
        exit 1
    fi
fi

# ── 3. Dependências de sistema para pygame (SDL2) ─────────────────────────────
# Verifica se libSDL2 já está instalada; instala só se necessário.
SDL_MISSING=false
if ! ldconfig -p 2>/dev/null | grep -q "libSDL2"; then
    SDL_MISSING=true
fi

if [ "$SDL_MISSING" = true ]; then
    echo -e "  ${YELLOW}→ Instalando dependências SDL2 (requer sudo)...${NC}"
    sudo apt-get install -y \
        libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
        libportmidi-dev libfreetype6-dev \
        python3-dev build-essential \
        2>/dev/null || true
fi

# ── 4. Criar / reutilizar ambiente virtual ────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo -e "  ${CYAN}→ Criando ambiente virtual em .venv/ ...${NC}"
    "$PYTHON" -m venv "$VENV_DIR"
    echo -e "  ${GREEN}✔${NC} Ambiente virtual criado."
else
    echo -e "  ${GREEN}✔${NC} Ambiente virtual existente em .venv/"
fi

# Ativar venv
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# ── 5. Instalar / atualizar pip ───────────────────────────────────────────────
echo -e "  ${CYAN}→ Verificando pip...${NC}"
"$VENV_PYTHON" -m pip install --upgrade pip --quiet

# ── 6. Instalar dependências do projeto ───────────────────────────────────────
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"

install_if_missing() {
    local pkg="$1"
    local import_name="${2:-$1}"
    if ! "$VENV_PYTHON" -c "import $import_name" &>/dev/null; then
        echo -e "  ${CYAN}→ Instalando ${BOLD}$pkg${NC}${CYAN}...${NC}"
        "$VENV_PIP" install "$pkg" --quiet
        echo -e "  ${GREEN}✔${NC} $pkg instalado."
    else
        local ver
        ver=$("$VENV_PYTHON" -c "import $import_name; print(getattr($import_name, '__version__', 'ok'))" 2>/dev/null)
        echo -e "  ${GREEN}✔${NC} $pkg já instalado ${BOLD}($ver)${NC}"
    fi
}

echo ""
echo -e "  ${BOLD}Dependências:${NC}"

if [ -f "$REQUIREMENTS" ]; then
    # Lê requirements.txt e instala cada pacote individualmente com verificação
    while IFS= read -r line || [ -n "$line" ]; do
        # Ignora comentários e linhas em branco
        [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
        # Extrai nome do pacote (remove versão e extras)
        pkg_name=$(echo "$line" | sed 's/[>=<!\[].*//')
        import_name="${pkg_name//-/_}"   # pygame-ce → pygame_ce (etc.)
        # Mapeamentos especiais
        case "$pkg_name" in
            pygame*)   import_name="pygame" ;;
            numpy*)    import_name="numpy"  ;;
        esac
        install_if_missing "$line" "$import_name"
    done < "$REQUIREMENTS"
else
    # Fallback: instala direto
    install_if_missing "pygame>=2.5.0" "pygame"
    install_if_missing "numpy>=1.24.0" "numpy"
fi

# ── 7. Verificação final ──────────────────────────────────────────────────────
echo ""
echo -e "  ${CYAN}→ Verificando imports...${NC}"

if ! "$VENV_PYTHON" - << 'PYCHECK'
import pygame, numpy
print(f"    pygame {pygame.version.ver} | numpy {numpy.__version__}")
PYCHECK
then
    echo -e "${RED}  ✗ Falha na verificação. Tente rodar novamente.${NC}"
    exit 1
fi

echo -e "  ${GREEN}✔${NC} Tudo pronto!"
echo ""

# ── 8. Iniciar o jogo ─────────────────────────────────────────────────────────
echo -e "  ${BOLD}${GREEN}▶  Iniciando Paper.io 2 — Edição Brasil...${NC}"
echo -e "  ${CYAN}  (feche a janela do jogo ou pressione ESC → Sair para encerrar)${NC}"
echo ""

# Executa a partir do diretório do projeto para que os caminhos relativos
# de assets/ e src/ sejam encontrados corretamente.
cd "$SCRIPT_DIR"
exec "$VENV_PYTHON" main.py
# exec substitui o processo shell pelo Python — o terminal volta ao prompt
# apenas depois que o jogo encerrar completamente.
PYEOF
chmod +x /home/claude/refactor/iniciar.sh
echo "iniciar.sh criado e marcado como executável"