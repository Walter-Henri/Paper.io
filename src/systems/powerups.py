# Responsabilidade:
# Gerenciar criação, spawn, coleta, efeitos e renderização dos power-ups.
# Controla os 5 itens coletáveis e o buff passivo de velocidade nas bordas.
# Não contém lógica de movimento de entidades, colisão ou lógica de câmera.

from __future__ import annotations
import pygame
import random
import math
from typing import List, Dict, Optional, Callable

from src.systems.sprite_manager import sprite_manager

# ── Identificadores de tipo ───────────────────────────────────────────────────
PU_SIZE_UP = "SIZE_UP"
PU_SPEED   = "SPEED"
PU_BOMB    = "BOMB"
PU_SHIELD  = "SHIELD"
PU_EAGLE   = "EAGLE"

POWERUP_DEFS: Dict[str, dict] = {
    PU_SIZE_UP: {"duration": 4.0,  "color": (255, 165,  0), "label": "EXPANSÃO", "sprite": "powerup.size_up"},
    PU_SPEED:   {"duration": 3.0,  "color": (0,   220, 255), "label": "TURBO",    "sprite": "powerup.speed"},
    PU_BOMB:    {"duration": 0.0,  "color": (255,  60,  60), "label": "BOMBA",    "sprite": "powerup.bomb"},
    PU_SHIELD:  {"duration": 3.0,  "color": (100, 255, 100), "label": "ESCUDO",   "sprite": "powerup.shield"},
    PU_EAGLE:   {"duration": 5.0,  "color": (200, 150, 255), "label": "VISÃO",    "sprite": "powerup.eagle"},
}

SPAWN_INTERVAL = 5.0   # segundos entre spawns
MAX_ITEMS      = 6
ITEM_RADIUS    = 14


# ── Item coletável ─────────────────────────────────────────────────────────────

class PowerUpItem:
    def __init__(self, kind: str, x: float, y: float):
        self.kind   = kind
        self.x      = x
        self.y      = y
        self.radius = ITEM_RADIUS
        self.alive  = True
        self._pulse = 0.0
        d           = POWERUP_DEFS[kind]
        self.color  = d["color"]
        self.label  = d["label"]
        self._sprite_key = d["sprite"]

    def update(self, dt: float) -> None:
        self._pulse += dt * 3.5

    def draw(self, surface: pygame.Surface,
             ox: float, oy: float) -> None:
        sx = int(self.x - ox)
        sy = int(self.y - oy)
        t  = math.sin(self._pulse) * 0.3 + 1.0
        r  = int(self.radius * t)

        # Tenta usar sprite configurado; fallback procedural
        sprite = sprite_manager.get(self._sprite_key)
        use_sprite = (sprite.get_width() > 2)   # sprite real tem mais de 2px

        if use_sprite:
            scaled = sprite_manager.get_scaled(self._sprite_key, r * 2, r * 2)
            surface.blit(scaled, (sx - r, sy - r))
        else:
            # Halo
            halo = pygame.Surface((r * 4 + 4, r * 4 + 4), pygame.SRCALPHA)
            pygame.draw.circle(halo, (*self.color, 50), (r*2+2, r*2+2), r + 6)
            surface.blit(halo, (sx - r*2 - 2, sy - r*2 - 2))
            # Sombra
            shadow = pygame.Surface((r*2+8, r*2+8), pygame.SRCALPHA)
            pygame.draw.circle(shadow, (0, 0, 0, 70), (r+4, r+4), r + 2)
            surface.blit(shadow, (sx - r - 4, sy - r - 4))
            # Corpo
            pygame.draw.circle(surface, (25, 25, 38), (sx, sy), r + 2)
            pygame.draw.circle(surface, self.color,   (sx, sy), r)
            hi = tuple(min(255, c + 90) for c in self.color)
            pygame.draw.circle(surface, hi, (sx - r//3, sy - r//3), r // 3)

    def emit_particles(self) -> List[dict]:
        pts = []
        for _ in range(14):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(55, 160)
            pts.append({
                "x": self.x, "y": self.y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": random.uniform(0.4, 0.75),
                "max_life": 0.75,
                "color": self.color,
                "size": random.randint(3, 7),
                "gravity": 20.0,
            })
        return pts


# ── Efeito ativo ───────────────────────────────────────────────────────────────

class ActiveEffect:
    def __init__(self, kind: str, duration: float):
        self.kind     = kind
        self.duration = duration
        self.elapsed  = 0.0

    def reset(self) -> None:
        self.elapsed = 0.0

    def update(self, dt: float) -> bool:
        """Retorna True enquanto o efeito estiver ativo."""
        if self.duration <= 0:
            return False
        self.elapsed += dt
        return self.elapsed < self.duration

    @property
    def fraction_left(self) -> float:
        if self.duration <= 0:
            return 0.0
        return max(0.0, 1.0 - self.elapsed / self.duration)

    @property
    def seconds_left(self) -> float:
        if self.duration <= 0:
            return 0.0
        return max(0.0, self.duration - self.elapsed)


# ── Partícula auxiliar interna ─────────────────────────────────────────────────

class _PUParticle:
    __slots__ = ("x","y","vx","vy","life","max_life","color","size","gravity")

    def __init__(self, d: dict):
        self.x        = d["x"];      self.y        = d["y"]
        self.vx       = d["vx"];     self.vy       = d["vy"]
        self.life     = d["life"];   self.max_life = d["max_life"]
        self.color    = d["color"];  self.size     = d["size"]
        self.gravity  = d.get("gravity", 0.0)

    def update(self, dt: float) -> bool:
        self.x  += self.vx * dt
        self.y  += self.vy * dt
        self.vy += self.gravity * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surface: pygame.Surface,
             ox: float, oy: float) -> None:
        t  = max(0.0, self.life / self.max_life)
        r  = max(1, int(self.size * (0.3 + 0.7 * t)))
        pygame.draw.circle(surface, self.color,
                           (int(self.x - ox), int(self.y - oy)), r)


# ── Gerenciador principal ──────────────────────────────────────────────────────

class PowerUpManager:
    """
    Controla ciclo de vida completo dos power-ups:
    spawn → coleta → efeitos ativos → expiração.
    """

    def __init__(self, world_width: float, world_height: float):
        self.ww = world_width
        self.wh = world_height
        self.items:      List[PowerUpItem]       = []
        self.active:     Dict[str, ActiveEffect] = {}
        self.particles:  List[_PUParticle]       = []
        self.bomb_anims: List[dict]              = []
        self._spawn_timer    = 0.0
        self._edge_linger    = 0.0
        self.edge_boost_on   = False

    # ── Spawn ──────────────────────────────────────────────────────────────────

    def _try_spawn(self) -> None:
        if len(self.items) >= MAX_ITEMS:
            return
        margin = 80
        kind = random.choice(list(POWERUP_DEFS.keys()))
        x    = random.uniform(margin, self.ww - margin)
        y    = random.uniform(margin, self.wh - margin)
        self.items.append(PowerUpItem(kind, x, y))

    # ── Update ─────────────────────────────────────────────────────────────────

    def update(self, dt: float,
               player_x: float, player_y: float,
               player_radius: float,
               player_on_edge: bool,
               claim_bomb_callback: Optional[Callable] = None,
               bots: Optional[list] = None,
               bot_bomb_callback: Optional[Callable] = None) -> None:
        """
        bots                – lista de entidades Bot (para coleta por IA)
        bot_bomb_callback   – função(bot, cx, cy, radius) chamada quando bot coleta bomba
        """

        # Spawn periódico
        self._spawn_timer += dt
        if self._spawn_timer >= SPAWN_INTERVAL:
            self._spawn_timer = 0.0
            self._try_spawn()

        # Coleta pelo jogador
        collected_by_player = []
        for item in self.items:
            item.update(dt)
            dist = math.hypot(player_x - item.x, player_y - item.y)
            if dist < player_radius + item.radius + 6:
                collected_by_player.append(item)

        for item in collected_by_player:
            if item in self.items:
                self.items.remove(item)
                for d in item.emit_particles():
                    self.particles.append(_PUParticle(d))
                self._apply(item.kind, player_x, player_y, claim_bomb_callback)

        # Coleta por bots (efeitos aplicados internamente via bot_effects)
        if bots:
            for bot in bots:
                if not bot.alive:
                    continue
                for item in list(self.items):
                    dist = math.hypot(bot.x - item.x, bot.y - item.y)
                    if dist < bot.radius + item.radius + 4:
                        self.items.remove(item)
                        for d in item.emit_particles():
                            self.particles.append(_PUParticle(d))
                        self._apply_to_bot(item.kind, bot,
                                           bot_bomb_callback)
                        break   # um item por bot por tick

        # Efeitos ativos
        expired = [k for k, e in self.active.items() if not e.update(dt)]
        for k in expired:
            del self.active[k]

        # Buff de borda: multiplica ×1.5 enquanto na borda + 1.5s de linger
        if player_on_edge:
            self._edge_linger  = 1.5
            self.edge_boost_on = True
        else:
            if self._edge_linger > 0:
                self._edge_linger -= dt
                self.edge_boost_on = True
            else:
                self.edge_boost_on = False

        # Partículas de coleta
        self.particles = [p for p in self.particles if p.update(dt)]

        # Animações de explosão da bomba
        for b in self.bomb_anims:
            b["t"] += dt * 2.5
        self.bomb_anims = [b for b in self.bomb_anims if b["t"] < 1.0]

    def _apply(self, kind: str, px: float, py: float,
               claim_bomb_callback: Optional[Callable]) -> None:
        d = POWERUP_DEFS[kind]
        if d["duration"] > 0:
            if kind in self.active:
                self.active[kind].reset()   # reinicia timer, não acumula
            else:
                self.active[kind] = ActiveEffect(kind, d["duration"])

        if kind == PU_BOMB and claim_bomb_callback:
            bomb_r = 90.0
            claim_bomb_callback(px, py, bomb_r)
            self.bomb_anims.append({
                "cx": px, "cy": py,
                "radius": bomb_r,
                "color": POWERUP_DEFS[PU_BOMB]["color"],
                "t": 0.0,
            })

    def _apply_to_bot(self, kind: str, bot,
                      bot_bomb_callback: Optional[Callable]) -> None:
        """Aplica efeito de power-up a um bot."""
        # Bots têm efeitos próprios armazenados em bot.bot_effects
        if not hasattr(bot, "bot_effects"):
            bot.bot_effects: Dict[str, ActiveEffect] = {}

        d = POWERUP_DEFS[kind]
        if d["duration"] > 0:
            if kind in bot.bot_effects:
                bot.bot_effects[kind].reset()
            else:
                bot.bot_effects[kind] = ActiveEffect(kind, d["duration"])

        if kind == PU_SPEED and d["duration"] > 0:
            # Aplica multiplicador de velocidade imediato
            from src.config.game_config import BOT_SPEED_BASE
            bot.speed = BOT_SPEED_BASE * (0.80 + 0.30 * bot.difficulty) * 2.0

        if kind == PU_BOMB and bot_bomb_callback:
            bomb_r = 90.0
            bot_bomb_callback(bot, bot.x, bot.y, bomb_r)
            self.bomb_anims.append({
                "cx": bot.x, "cy": bot.y,
                "radius": bomb_r,
                "color": POWERUP_DEFS[PU_BOMB]["color"],
                "t": 0.0,
            })

    def update_bot_effects(self, dt: float, bots: list) -> None:
        """Atualiza efeitos temporários dos bots e reverte ao expirar."""
        from src.config.game_config import BOT_SPEED_BASE
        for bot in bots:
            if not bot.alive or not hasattr(bot, "bot_effects"):
                continue
            expired = []
            for kind, eff in bot.bot_effects.items():
                if not eff.update(dt):
                    expired.append(kind)
            for k in expired:
                del bot.bot_effects[k]
                # Reverter velocidade ao expirar SPEED
                if k == PU_SPEED:
                    bot.speed = BOT_SPEED_BASE * (0.80 + 0.30 * bot.difficulty)

    # ── Propriedades de modificadores ──────────────────────────────────────────

    def has(self, kind: str) -> bool:
        return kind in self.active

    @property
    def speed_multiplier(self) -> float:
        m = 1.0
        if self.has(PU_SPEED):
            m *= 2.0
        if self.edge_boost_on:
            m *= 1.5
        return m

    @property
    def size_multiplier(self) -> float:
        return 2.0 if self.has(PU_SIZE_UP) else 1.0

    @property
    def shield_active(self) -> bool:
        return self.has(PU_SHIELD)

    @property
    def eagle_active(self) -> bool:
        return self.has(PU_EAGLE)

    # ── Renderização no mundo ──────────────────────────────────────────────────

    def draw_world(self, surface: pygame.Surface,
                   ox: float, oy: float) -> None:
        # Animações de explosão da bomba
        for b in self.bomb_anims:
            cx    = int(b["cx"] - ox)
            cy    = int(b["cy"] - oy)
            r     = int(b["radius"] * b["t"])
            alpha = int(255 * (1.0 - b["t"]))
            if r > 0:
                s = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
                pygame.draw.circle(s, (*b["color"], alpha),   (r+2, r+2), r,   4)
                pygame.draw.circle(s, (*b["color"], alpha//4),(r+2, r+2), r)
                surface.blit(s, (cx - r - 2, cy - r - 2))

        # Partículas
        for p in self.particles:
            p.draw(surface, ox, oy)

        # Itens
        for item in self.items:
            item.draw(surface, ox, oy)

    # ── Painel HUD de efeitos ativos ───────────────────────────────────────────

    def draw_hud(self, surface: pygame.Surface,
                 font_sm: pygame.font.Font,
                 font_xs: pygame.font.Font,
                 screen_w: int, screen_h: int) -> None:
        slots = [(k, e) for k, e in self.active.items()]
        if self.edge_boost_on:
            slots.append(("EDGE", None))
        if not slots:
            return

        bar_w = 88
        bar_h = 7
        gap   = 96
        x0    = 10
        y_base = screen_h - 68

        for i, (kind, eff) in enumerate(slots):
            x = x0 + i * gap
            if kind == "EDGE":
                color = (255, 220, 0)
                label = "BORDA"
                frac  = 1.0
                secs  = ""
            else:
                d     = POWERUP_DEFS[kind]
                color = d["color"]
                label = d["label"]
                frac  = eff.fraction_left
                secs  = f"{eff.seconds_left:.1f}s"

            panel = pygame.Surface((bar_w + 4, 46), pygame.SRCALPHA)
            panel.fill((15, 15, 25, 185))
            surface.blit(panel, (x - 2, y_base - 20))

            lbl = font_xs.render(label, True, color)
            surface.blit(lbl, (x, y_base - 18))

            pygame.draw.rect(surface, (55, 55, 70),
                             (x, y_base, bar_w, bar_h), border_radius=3)
            if frac > 0:
                fw = max(2, int(bar_w * frac))
                pygame.draw.rect(surface, color,
                                 (x, y_base, fw, bar_h), border_radius=3)
            if secs:
                ts = font_xs.render(secs, True, (210, 210, 210))
                surface.blit(ts, (x + bar_w - ts.get_width(), y_base - 18))
