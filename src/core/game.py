# Responsabilidade:
# Gerenciar o ciclo completo de uma partida: mundo, entidades, colisões,
# power-ups, câmera, partículas, renderização do mundo e condições de vitória.
# Integra todos os sistemas sem concentrar lógica interna de cada um.
# Não contém lógica de menus, fontes ou persistência de dados.

from __future__ import annotations
import random
import math
import pygame
from typing import List

from src.config.difficulty  import get_profile, promote_tier, evolve_for_level
from src.config.game_config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT,
    CELL_SIZE, WORLD_COLS, WORLD_ROWS, BG_COLOR, GRID_COLOR,
    SKINS, NUM_BOTS, BOT_NAMES, PLAYER_RADIUS, PLAYER_SPEED,
    CAMERA_LERP,
)
from src.entities.world     import World
from src.entities.player    import Player, Entity
from src.entities.bot       import Bot
from src.systems.camera     import Camera
from src.systems.collision  import check_collisions
from src.systems.particles  import ParticleSystem
from src.systems.powerups   import PowerUpManager
from src.core.brazil_maps   import STATE_ORDER


class GameSession:
    """
    Encapsula uma única partida: criação, update e draw.
    Instanciada pela máquina de estados em main.py ao entrar no estado PLAYING.
    """

    def __init__(self, skin: dict, level: int):
        self.skin  = skin
        self.level = level
        idx        = (level - 1) % len(STATE_ORDER)
        self.state_name = STATE_ORDER[idx]

        # Sistemas
        self.world     = World()
        self.particles = ParticleSystem()
        self.camera    = Camera()
        self.pu_manager = PowerUpManager(WORLD_WIDTH, WORLD_HEIGHT)

        # Entidades
        Entity._next_id = 1
        self.entities:  List[Entity] = []
        self.player:    Player       = self._spawn_player()
        self.bots:      List[Bot]    = self._spawn_bots()

        # Mapa de cores (entity.id → color) para renderização do território
        self._color_map: dict = {e.id: e.color for e in self.entities}

        # Câmera imediata no jogador
        self.camera.follow(self.player.x, self.player.y, lerp=1.0)

        # Estado interno
        self.finished  = False
        self.won       = False
        self._predator_notified = False
        self.notifications: List[dict] = []

    # ── Inicialização ──────────────────────────────────────────────────────────

    def _spawn_player(self) -> Player:
        px, py = WORLD_WIDTH * 0.5, WORLD_HEIGHT * 0.5
        p = Player(px, py, self.skin)
        self.world.seed_starting_territory(px, py, p.id, radius_cells=9)
        self.entities.append(p)
        return p

    def _spawn_bots(self) -> List[Bot]:
        bots       = []
        px, py     = self.player.x, self.player.y
        used_skins = {self.skin["id"]}
        names      = random.sample(BOT_NAMES, min(NUM_BOTS, len(BOT_NAMES)))

        for i in range(NUM_BOTS):
            # Posição que não sobreponha o jogador
            for _ in range(300):
                bx = random.uniform(80, WORLD_WIDTH  - 80)
                by = random.uniform(80, WORLD_HEIGHT - 80)
                if abs(bx - px) > 220 or abs(by - py) > 220:
                    break
            available = [s for s in SKINS if s["id"] not in used_skins] or SKINS
            skin      = random.choice(available)
            used_skins.add(skin["id"])
            # Tier sobe com a fase; o perfil ainda é afiado dentro do tier.
            diff_pool = (["facil"] * 2 + ["medio"] * 4 + ["dificil"] * 2)
            diff_name = promote_tier(diff_pool[i % len(diff_pool)], self.level)
            profile   = evolve_for_level(get_profile(diff_name), self.level)
            bot = Bot(bx, by, skin,
                      name=names[i % len(names)],
                      difficulty_profile=profile)
            self.world.seed_starting_territory(bx, by, bot.id, radius_cells=6)
            self.entities.append(bot)
            bots.append(bot)
        return bots

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float, keys) -> None:
        if self.finished:
            return

        # Input do jogador + multiplicador de velocidade de power-up
        self.player.handle_input(keys)
        self.player.speed = PLAYER_SPEED * self.pu_manager.speed_multiplier

        # Atualiza todas as entidades
        pu_items = self.pu_manager.items  # lista de itens disponíveis para os bots
        for e in self.entities:
            if not e.alive:
                if e.death_timer > 0:
                    e.death_timer -= dt
                continue
            if isinstance(e, Bot):
                e.update_ai(dt, self.world, self.entities, powerup_items=pu_items)
            e.update_position(dt)
            claimed = e.update_trail_and_claim(self.world)
            if claimed > 0 and e.just_claimed:
                trail_pts = e.trail.points or [(e.x, e.y)]
                self.particles.emit_claim(trail_pts, e.color)
                self.particles.emit_burst(e.x, e.y, e.color,
                                          count=12, speed=80, life=0.5)

        # Colisões
        kills = check_collisions(
            self.entities,
            self.player,
            self.pu_manager.shield_active,
        )
        for killer, victim in kills:
            if not victim.alive:
                continue
            self.particles.emit_death(victim.x, victim.y, victim.color)
            self.world.clear_owner(victim.id)
            victim.kill()
            if killer is not victim:
                killer.kills += 1
                if killer is self.player:
                    self._push_notif(f"Eliminou {victim.name}!", (100, 255, 100))

        # Power-ups (jogador + bots)
        on_edge = self._player_on_edge()
        self.pu_manager.update(
            dt,
            self.player.x, self.player.y,
            PLAYER_RADIUS * self.pu_manager.size_multiplier,
            on_edge,
            claim_bomb_callback=self._bomb_claim,
            bots=self.bots,
            bot_bomb_callback=self._bot_bomb_claim,
        )
        self.pu_manager.update_bot_effects(dt, self.bots)

        # Pontuação
        for e in self.entities:
            if e.alive:
                e.score_percent = self.world.ownership_percent(e.id)

        # Partículas e notificações
        self.particles.update(dt)
        for n in self.notifications:
            n["life"] -= dt
        self.notifications = [n for n in self.notifications if n["life"] > 0]

        # Predador
        if self.player.kills >= 4 and not self._predator_notified:
            self._predator_notified = True
            self._push_notif("⚡ PREDADOR DESBLOQUEADO!", (255, 60, 60))

        # Câmera
        if self.player.alive:
            cam_lerp = 0.08 if self.pu_manager.eagle_active else CAMERA_LERP
            self.camera.follow(self.player.x, self.player.y, lerp=cam_lerp)

        # Condições de fim
        if not self.player.alive:
            self._finish(won=False)
            return
        alive_others = [e for e in self.entities
                        if e.alive and e is not self.player]
        if not alive_others or self.player.score_percent >= 100.0:
            self._finish(won=True)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _player_on_edge(self) -> bool:
        m = PLAYER_RADIUS + 4
        return (self.player.x <= m or
                self.player.x >= WORLD_WIDTH  - m or
                self.player.y <= m or
                self.player.y >= WORLD_HEIGHT - m)

    def _bomb_claim(self, cx: float, cy: float, radius: float) -> None:
        min_gx = max(0,            int((cx - radius) / CELL_SIZE))
        max_gx = min(WORLD_COLS-1, int((cx + radius) / CELL_SIZE) + 1)
        min_gy = max(0,            int((cy - radius) / CELL_SIZE))
        max_gy = min(WORLD_ROWS-1, int((cy + radius) / CELL_SIZE) + 1)
        r2     = radius * radius
        for gx in range(min_gx, max_gx + 1):
            for gy in range(min_gy, max_gy + 1):
                wx = (gx + 0.5) * CELL_SIZE
                wy = (gy + 0.5) * CELL_SIZE
                if (wx - cx)**2 + (wy - cy)**2 <= r2:
                    self.world.set_owner_cell(gx, gy, self.player.id)
        self.particles.emit_burst(cx, cy, (255, 80, 60),
                                  count=25, speed=160, life=0.6)
        self._push_notif("BOMBA DE TINTA!", (255, 80, 60))

    def _bot_bomb_claim(self, bot, cx: float, cy: float, radius: float) -> None:
        """Bomba de tinta explodida por um bot: conquista área para o bot."""
        min_gx = max(0,            int((cx - radius) / CELL_SIZE))
        max_gx = min(WORLD_COLS-1, int((cx + radius) / CELL_SIZE) + 1)
        min_gy = max(0,            int((cy - radius) / CELL_SIZE))
        max_gy = min(WORLD_ROWS-1, int((cy + radius) / CELL_SIZE) + 1)
        r2 = radius * radius
        for gx in range(min_gx, max_gx + 1):
            for gy in range(min_gy, max_gy + 1):
                wx = (gx + 0.5) * CELL_SIZE
                wy = (gy + 0.5) * CELL_SIZE
                if (wx - cx)**2 + (wy - cy)**2 <= r2:
                    self.world.set_owner_cell(gx, gy, bot.id)
        self.particles.emit_burst(cx, cy, bot.color, count=20, speed=160, life=0.5)

    def _finish(self, won: bool) -> None:
        self.finished = True
        self.won      = won

    def _push_notif(self, text: str,
                    color: tuple = (255, 255, 100)) -> None:
        self.notifications.append({"text": text, "color": color, "life": 2.5})

    # ── Renderização ──────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface,
             assets, paused: bool = False) -> None:
        surface.fill(BG_COLOR)
        ox, oy = self.camera.offset()

        if self.pu_manager.eagle_active:
            self._draw_eagle_view(surface)
        else:
            self._draw_grid(surface, ox, oy)
            self._draw_world_border(surface, ox, oy)
            self._draw_territory(surface, ox, oy)
            for e in self.entities:
                if e.alive or e.death_timer > 0:
                    e.draw(surface, (ox, oy))
            self.particles.draw(surface, ox, oy)
            self.pu_manager.draw_world(surface, ox, oy)

        if self.pu_manager.shield_active:
            self._draw_shield_vfx(surface, ox, oy)

    # ── Componentes de draw ───────────────────────────────────────────────────

    def _draw_grid(self, surface: pygame.Surface,
                   ox: float, oy: float) -> None:
        step    = CELL_SIZE * 4
        start_x = int(ox) - (int(ox) % step)
        start_y = int(oy) - (int(oy) % step)
        for x in range(start_x, int(ox) + SCREEN_WIDTH + step, step):
            sx = x - int(ox)
            pygame.draw.line(surface, GRID_COLOR, (sx, 0), (sx, SCREEN_HEIGHT))
        for y in range(start_y, int(oy) + SCREEN_HEIGHT + step, step):
            sy = y - int(oy)
            pygame.draw.line(surface, GRID_COLOR, (0, sy), (SCREEN_WIDTH, sy))

    def _draw_world_border(self, surface: pygame.Surface,
                            ox: float, oy: float) -> None:
        x0 = int(-ox) + 2
        y0 = int(-oy) + 2
        w  = WORLD_WIDTH  - 4
        h  = WORLD_HEIGHT - 4
        for i in range(6, 0, -1):
            alpha = 15 + i * 14
            gs    = pygame.Surface((w + i*4, h + i*4), pygame.SRCALPHA)
            pygame.draw.rect(gs, (60, 100, 220, alpha),
                             gs.get_rect(), i * 2, border_radius=4)
            surface.blit(gs, (x0 - i*2, y0 - i*2))
        pygame.draw.rect(surface, (90, 130, 255), (x0, y0, w, h), 3, border_radius=2)
        cl = 24
        cc = (160, 200, 255)
        for cx2, cy2 in [(x0,y0),(x0+w,y0),(x0,y0+h),(x0+w,y0+h)]:
            dx2 = 1 if cx2 == x0 else -1
            dy2 = 1 if cy2 == y0 else -1
            pygame.draw.line(surface, cc, (cx2, cy2), (cx2+dx2*cl, cy2), 3)
            pygame.draw.line(surface, cc, (cx2, cy2), (cx2, cy2+dy2*cl), 3)

    def _draw_territory(self, surface: pygame.Surface,
                         ox: float, oy: float) -> None:
        sc  = max(0, int(ox // CELL_SIZE) - 1)
        ec  = min(WORLD_COLS, int((ox + SCREEN_WIDTH)  // CELL_SIZE) + 2)
        sr  = max(0, int(oy // CELL_SIZE) - 1)
        er  = min(WORLD_ROWS, int((oy + SCREEN_HEIGHT) // CELL_SIZE) + 2)
        for cy in range(sr, er):
            base = cy * WORLD_COLS
            for cx in range(sc, ec):
                owner = self.world.grid[base + cx]
                if not owner:
                    continue
                color = self._color_map.get(owner)
                if not color:
                    continue
                fill = (max(0,color[0]-35),
                        max(0,color[1]-35),
                        max(0,color[2]-35))
                pygame.draw.rect(surface, fill,
                    (int(cx*CELL_SIZE - ox),
                     int(cy*CELL_SIZE - oy),
                     CELL_SIZE, CELL_SIZE))

    def _draw_eagle_view(self, surface: pygame.Surface) -> None:
        scale = min(SCREEN_WIDTH / WORLD_WIDTH,
                    SCREEN_HEIGHT / WORLD_HEIGHT) * 1.65
        off_x = (SCREEN_WIDTH  - WORLD_WIDTH  * scale) / 2
        off_y = (SCREEN_HEIGHT - WORLD_HEIGHT * scale) / 2
        step  = 3
        for cy in range(0, WORLD_ROWS, step):
            for cx in range(0, WORLD_COLS, step):
                owner = self.world.grid[cy * WORLD_COLS + cx]
                if not owner:
                    continue
                color = self._color_map.get(owner)
                if not color:
                    continue
                fill = (max(0,color[0]-30),max(0,color[1]-30),max(0,color[2]-30))
                sx   = int(cx * CELL_SIZE * scale + off_x)
                sy   = int(cy * CELL_SIZE * scale + off_y)
                size = max(2, int(CELL_SIZE * step * scale))
                pygame.draw.rect(surface, fill, (sx, sy, size, size))
        pygame.draw.rect(surface, (90, 130, 255),
            (int(off_x), int(off_y),
             int(WORLD_WIDTH*scale), int(WORLD_HEIGHT*scale)), 3)
        for e in self.entities:
            if not e.alive:
                continue
            sx = int(e.x * scale + off_x)
            sy = int(e.y * scale + off_y)
            r  = max(4, int(PLAYER_RADIUS * scale * 1.5))
            pygame.draw.circle(surface, (20,20,30), (sx,sy), r+2)
            pygame.draw.circle(surface, e.color,    (sx,sy), r)
            if e is self.player:
                pygame.draw.circle(surface,(255,255,255),(sx,sy),r,2)
        if self.pu_manager:
            for item in self.pu_manager.items:
                sx = int(item.x * scale + off_x)
                sy = int(item.y * scale + off_y)
                pygame.draw.circle(surface, item.color, (sx,sy), 7)
                pygame.draw.circle(surface,(255,255,255),(sx,sy),7,1)

    def _draw_shield_vfx(self, surface: pygame.Surface,
                          ox: float, oy: float) -> None:
        t  = pygame.time.get_ticks() / 300.0
        r  = PLAYER_RADIUS + 11 + int(math.sin(t) * 4)
        sx = int(self.player.x - ox)
        sy = int(self.player.y - oy)
        alpha = int(155 + 65 * math.sin(t))
        ss = pygame.Surface((r*2+8, r*2+8), pygame.SRCALPHA)
        pygame.draw.circle(ss, (100,255,100,alpha),(r+4,r+4), r,  3)
        pygame.draw.circle(ss, (100,255,100,alpha//3),(r+4,r+4),r-4,2)
        surface.blit(ss, (sx-r-4, sy-r-4))
