# Responsabilidade:
# Criar, atualizar, renderizar e destruir partículas visuais.
# Oferece emissores de burst, trilha e morte.
# Não contém lógica de jogo, colisão ou comportamento de entidades.

from __future__ import annotations
from typing import List, Tuple
import random
import math
import pygame


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life",
                 "color", "size", "gravity")

    def __init__(self, x: float, y: float, vx: float, vy: float,
                 life: float, color: Tuple[int, int, int],
                 size: int = 3, gravity: float = 0.0):
        self.x        = x
        self.y        = y
        self.vx       = vx
        self.vy       = vy
        self.life     = life
        self.max_life = life
        self.color    = color
        self.size     = size
        self.gravity  = gravity

    def update(self, dt: float) -> bool:
        self.x  += self.vx * dt
        self.y  += self.vy * dt
        self.vy += self.gravity * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surface: pygame.Surface, ox: float, oy: float) -> None:
        t  = max(0.0, self.life / self.max_life)
        s  = max(1, int(self.size * (0.4 + 0.6 * t)))
        sx = int(self.x - ox)
        sy = int(self.y - oy)
        pygame.draw.circle(surface, self.color, (sx, sy), s)


class ParticleSystem:
    def __init__(self, max_particles: int = 800):
        self.particles: List[Particle] = []
        self.max_particles = max_particles

    def clear(self) -> None:
        self.particles.clear()

    def _add(self, p: Particle) -> None:
        if len(self.particles) >= self.max_particles:
            self.particles.pop(0)
        self.particles.append(p)

    def emit_burst(self, x: float, y: float,
                   color: Tuple[int, int, int],
                   count: int = 20,
                   speed: float = 120.0,
                   life: float = 0.6) -> None:
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            sp    = random.uniform(speed * 0.3, speed)
            self._add(Particle(
                x, y,
                math.cos(angle) * sp,
                math.sin(angle) * sp,
                random.uniform(life * 0.5, life),
                color,
                size=random.randint(2, 5),
                gravity=random.uniform(0, 40),
            ))

    def emit_claim(self, points: List[Tuple[float, float]],
                   color: Tuple[int, int, int]) -> None:
        """Faíscas ao longo dos pontos de um polígono capturado."""
        if not points:
            return
        step = max(1, len(points) // 25)
        for i in range(0, len(points), step):
            px, py = points[i]
            self.emit_burst(px, py, color, count=4, speed=60, life=0.45)

    def emit_death(self, x: float, y: float,
                   color: Tuple[int, int, int]) -> None:
        self.emit_burst(x, y, color,          count=35, speed=180, life=0.85)
        self.emit_burst(x, y, (255, 255, 255), count=12, speed=100, life=0.5)

    def update(self, dt: float) -> None:
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface: pygame.Surface,
             ox: float, oy: float) -> None:
        for p in self.particles:
            p.draw(surface, ox, oy)
