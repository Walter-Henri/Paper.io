
from __future__ import annotations
from typing import Tuple, Optional
import pygame

from src.config.game_config import (
    PLAYER_SPEED, PLAYER_RADIUS, TRAIL_WIDTH, TRAIL_SAMPLE_DIST,
    DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT,
    MIN_CLAIM_POINTS, CLOSE_THRESHOLD,
)
from src.entities.trail         import Trail
from src.systems.sprite_manager import sprite_manager


class Entity:
    _next_id = 1
    _label_font = None

    def __init__(self, x: float, y: float,
                 color:     Tuple[int, int, int],
                 speed:     float,
                 name:      str = "",
                 secondary: Optional[Tuple[int, int, int]] = None,
                 accent:    Optional[Tuple[int, int, int]] = None):
        self.id        = Entity._next_id
        Entity._next_id += 1
        self.x         = x
        self.y         = y
        self.color     = color
        self.secondary = secondary or tuple(max(0, c - 50) for c in color)
        self.accent    = accent    or (255, 255, 255)
        self.speed     = speed
        self.name      = name or f"P{self.id}"
        self.alive     = True
        self.direction = DIR_RIGHT
        self.trail     = Trail(self.id, color)
        self.outside   = False
        self.score_percent        = 0.0
        self.kills                = 0
        self.cells_claimed_total  = 0
        self.drawing   = False
        self.just_claimed = False
        self.death_timer  = 0.0
        self.slide_sign   = 0

    # Raio de colisão
    @property
    def radius(self) -> int:
        """Raio lógico da entidade para colisão e detecção de proximidade."""
        return PLAYER_RADIUS

    # Direção
    def set_direction(self, dx: int, dy: int) -> None:
        # Permite virar 180° e voltar pelo mesmo caminho.
        if dx == 0 and dy == 0:
            return
        self.direction = (dx, dy)

    # Movimentação

    # Trilha e captura
    def update_trail_and_claim(self, world) -> int:
        """Retorna número de células capturadas neste frame."""
        self.just_claimed = False
        if not self.alive:
            return 0

        own = world.is_own_territory(self.x, self.y, self.id)

        if own:
            if self.outside and len(self.trail.points) >= MIN_CLAIM_POINTS:
                self.trail.add_point(self.x, self.y, min_dist=0)
                claimed = world.claim_polygon(self.trail.points, self.id)
                self.cells_claimed_total += claimed
                self.trail.clear()
                self.outside      = False
                self.drawing      = False
                self.just_claimed = claimed > 0
                return claimed
            else:
                self.trail.clear()
                self.outside = False
                self.drawing = False
        else:
            # Fechar loop aproximando-se do ponto inicial
            if (self.outside
                    and len(self.trail.points) >= MIN_CLAIM_POINTS
                    and self.trail.is_near_start(self.x, self.y, CLOSE_THRESHOLD)):
                self.trail.add_point(self.x, self.y, min_dist=0)
                self.trail.points.append(self.trail.points[0])
                claimed = world.claim_polygon(self.trail.points, self.id)
                self.cells_claimed_total += claimed
                self.trail.clear()
                self.outside      = False
                self.drawing      = False
                self.just_claimed = claimed > 0
                return claimed

            self.outside = True
            self.drawing = True
            self.trail.add_point(self.x, self.y, TRAIL_SAMPLE_DIST)

        return 0

    # Morte
    def kill(self) -> None:
        self.alive        = False
        self.trail.active = False
        self.drawing      = False
        self.death_timer  = 0.8

    # Renderização
    def draw(self, surface: pygame.Surface,
             camera_offset: Tuple[float, float]) -> None:
        ox, oy = camera_offset

        # Trilha
        if len(self.trail.points) >= 2 and (self.alive or self.death_timer > 0):
            pts = [(int(p[0] - ox), int(p[1] - oy))
                   for p in self.trail.points]
            pygame.draw.lines(surface, self.secondary, False, pts, TRAIL_WIDTH + 4)
            pygame.draw.lines(surface, self.color,     False, pts, TRAIL_WIDTH)
            core = tuple(min(255, c + 50) for c in self.color)
            pygame.draw.lines(surface, core, False, pts, max(1, TRAIL_WIDTH - 2))

        if not self.alive:
            return

        sx = int(self.x - ox)
        sy = int(self.y - oy)
        r  = PLAYER_RADIUS

        # Tenta usar sprite configurado; fallback procedural
        sprite     = sprite_manager.get("player.default")
        use_sprite = sprite.get_width() > 2

        if use_sprite:
            diam   = r * 2 + 6
            scaled = sprite_manager.get_scaled("player.default", diam, diam)
            surface.blit(scaled, (sx - diam // 2, sy - diam // 2))
        else:
            # Glow disc
            gr    = r + 6
            gsurf = pygame.Surface((gr * 2 + 2, gr * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(gsurf, (*self.color[:3], 55), (gr+1, gr+1), gr)
            surface.blit(gsurf, (sx-gr-1, sy-gr-1),
                         special_flags=pygame.BLEND_ALPHA_SDL2)
            # Camadas do corpo
            pygame.draw.circle(surface, self.secondary, (sx, sy), r + 3)
            pygame.draw.circle(surface, self.color,     (sx, sy), r)
            pygame.draw.circle(surface, self.accent,    (sx, sy), r,     2)
            pygame.draw.circle(surface, self.accent,    (sx-2, sy-2),    3)

        # Indicador de direção
        dx, dy = self.direction
        pygame.draw.circle(surface, (255, 255, 255),
                           (sx + int(dx * 5), sy + int(dy * 5)), 3)
        self.draw_name_tag(surface, sx, sy, r)

    def draw_name_tag(self, surface: pygame.Surface,
                      sx: int, sy: int, radius: int,
                      extra_lift: int = 0) -> None:
        """Nickname flutuante acima da entidade."""
        if not self.alive or not self.name:
            return
        if Entity._label_font is None:
            Entity._label_font = pygame.font.Font(None, 18)
        font = Entity._label_font
        text = font.render(self.name, True, (245, 248, 255))
        tw, th = text.get_size()
        lx = sx - tw // 2
        ly = sy - radius - th - 6 - extra_lift
        pad = 3
        bg = pygame.Surface((tw + pad * 2, th + 2), pygame.SRCALPHA)
        bg.fill((8, 10, 16, 170))
        surface.blit(bg, (lx - pad, ly - 1))
        surface.blit(text, (lx, ly))


class Player(Entity):
    """Jogador controlado pelo humano."""

    def __init__(self, x: float, y: float, skin: dict):
        super().__init__(
            x, y,
            skin["primary"],
            PLAYER_SPEED,
            name="Você",
            secondary=skin["secondary"],
            accent=skin["accent"],
        )
        self.skin_id   = skin["id"]
        self.skin_name = skin["name"]

    def handle_input(self, keys) -> None:
        if   keys[pygame.K_UP]    or keys[pygame.K_w]: self.set_direction(*DIR_UP)
        elif keys[pygame.K_DOWN]  or keys[pygame.K_s]: self.set_direction(*DIR_DOWN)
        elif keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.set_direction(*DIR_LEFT)
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.set_direction(*DIR_RIGHT)
