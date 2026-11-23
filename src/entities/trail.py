# Responsabilidade:
# Representar e gerenciar a trilha deixada por uma entidade
# enquanto ela se move fora do próprio território.
# Armazena pontos, controla distância mínima entre amostras
# e verifica proximidade ao ponto inicial (para fechar o loop).
# Não contém lógica de jogo, colisão ou renderização.

from __future__ import annotations
from typing import List, Tuple
import math

Point = Tuple[float, float]


class Trail:
    def __init__(self, owner_id: int, color: Tuple[int, int, int]):
        self.owner_id = owner_id
        self.color    = color
        self.points:  List[Point] = []
        self.active   = True

    def add_point(self, x: float, y: float,
                  min_dist: float = 3.5) -> None:
        if not self.points:
            self.points.append((x, y))
            return
        last   = self.points[-1]
        dx, dy = x - last[0], y - last[1]
        if dx * dx + dy * dy >= min_dist * min_dist:
            self.points.append((x, y))

    def clear(self) -> None:
        self.points.clear()
        self.active = True

    def length(self) -> float:
        if len(self.points) < 2:
            return 0.0
        total = 0.0
        for i in range(1, len(self.points)):
            dx = self.points[i][0] - self.points[i-1][0]
            dy = self.points[i][1] - self.points[i-1][1]
            total += math.hypot(dx, dy)
        return total

    def is_near_start(self, x: float, y: float,
                      threshold: float = 22.0) -> bool:
        if len(self.points) < 4:
            return False
        sx, sy = self.points[0]
        return (x - sx)**2 + (y - sy)**2 <= threshold * threshold
