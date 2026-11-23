"""
log_setup.py — TerritórIO: Edição Brasil
-----------------------------------------
Responsabilidade:
    Configurar o módulo nativo `logging` do Python para o projeto.
    Define nível, formato e destinos (console + arquivo opcional).
    Deve ser chamado uma única vez, antes de qualquer import de módulos
    do jogo que usem logging.

Uso:
    from src.core.log_setup import configure_logging
    configure_logging(debug=False)   # produção
    configure_logging(debug=True)    # desenvolvimento — verbose

Não contém lógica de jogo nem dependências de Pygame.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent


def configure_logging(debug: bool = False,
                      log_file: str | None = None) -> None:
    """
    Configura o logging global do projeto.

    Parâmetros:
        debug    — True ativa nível DEBUG (verbose); False usa INFO
        log_file — caminho para arquivo de log adicional (opcional)

    Formato de saída:
        [LEVEL] modulo: mensagem
    """
    level  = logging.DEBUG if debug else logging.INFO
    fmt    = "[%(levelname)s] %(name)s: %(message)s"
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout)
    ]

    if log_file:
        path = _ROOT / log_file
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(fmt))
        handlers.append(file_handler)

    logging.basicConfig(level=level, format=fmt, handlers=handlers, force=True)

    # Silenciar ruído de módulos externos
    logging.getLogger("pygame").setLevel(logging.WARNING)
