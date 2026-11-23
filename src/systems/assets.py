# Responsabilidade:
# Carregar e disponibilizar fontes tipográficas do jogo.
# Centraliza o acesso às fontes Kenney Future (CC0).
# Não contém lógica de jogo, sprites (ver sprite_manager) ou áudio (ver audio.py).

from __future__ import annotations
import os
import pygame
from typing import Dict

_ROOT      = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_FONTS_DIR = os.path.join(_ROOT, "assets", "fonts")


class Assets:
    def __init__(self):
        self.fonts: Dict[str, pygame.font.Font] = {}
        self._load_fonts()

    def _load_fonts(self) -> None:
        specs = [
            ("title",    "Kenney Future.ttf",        56),
            ("title_sm", "Kenney Future.ttf",        36),
            ("body",     "Kenney Future Narrow.ttf", 28),
            ("small",    "Kenney Future Narrow.ttf", 18),
            ("tiny",     "Kenney Future Narrow.ttf", 14),
        ]
        for name, filename, size in specs:
            path = os.path.join(_FONTS_DIR, filename)
            try:
                if os.path.isfile(path):
                    self.fonts[name] = pygame.font.Font(path, size)
                else:
                    self.fonts[name] = pygame.font.SysFont(
                        "Arial", size, bold=name.startswith("title"))
            except Exception:
                self.fonts[name] = pygame.font.SysFont("Arial", size)

    def font(self, name: str) -> pygame.font.Font:
        return (self.fonts.get(name)
                or self.fonts.get("body")
                or pygame.font.SysFont("Arial", 24))
