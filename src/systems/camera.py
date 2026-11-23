# Responsabilidade:
# Gerenciar o acompanhamento suave da câmera ao jogador,
# zoom para o Eagle Eye e transformações de coordenadas mundo→tela.
# Não contém lógica de jogo, colisão ou renderização de entidades.

from __future__ import annotations
from typing import Tuple
from src.config.game_config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, CAMERA_LERP
)


class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0

    def follow(self, target_x: float, target_y: float,
               lerp: float = CAMERA_LERP) -> None:
        desired_x = target_x - SCREEN_WIDTH  / 2
        desired_y = target_y - SCREEN_HEIGHT / 2
        self.x += (desired_x - self.x) * lerp
        self.y += (desired_y - self.y) * lerp
        self.x = max(0.0, min(max(0.0, WORLD_WIDTH  - SCREEN_WIDTH),  self.x))
        self.y = max(0.0, min(max(0.0, WORLD_HEIGHT - SCREEN_HEIGHT), self.y))

    def offset(self) -> Tuple[float, float]:
        return self.x, self.y

    def world_to_screen(self, wx: float, wy: float) -> Tuple[int, int]:
        return int(wx - self.x), int(wy - self.y)
