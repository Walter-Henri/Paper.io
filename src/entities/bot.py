"""
bot.py — TerritórIO: Edição Brasil
------------------------------------
Responsabilidade:
    Implementar a IA dos bots usando máquina de estados finitos (FSM)
    com avaliação de utilidade em 6 estados:
        expand, return, hunt, intercept, evade, collect_pu

    Integra DifficultyProfile para suportar 3 níveis de dificuldade
    configuráveis sem alterar artificialmente a velocidade.

    Bots coletam power-ups de forma estratégica quando o perfil permite.
    Renderiza com sprite_manager (sprite real ou fallback procedural).

Não contém lógica do jogador humano, power-ups globais ou colisão global.
"""

from __future__ import annotations

import logging
import math
import random
from typing import Any, List, Optional, Tuple

import pygame

from src.config.difficulty import DEFAULT_DIFFICULTY, DifficultyProfile, get_profile
from src.config.game_config import (
    AI_DANGER_RANGE, AI_HUNT_RANGE,
    BOT_SPEED_BASE, CELL_SIZE,
    DIRECTIONS, PLAYER_RADIUS, TRAIL_WIDTH,
    WORLD_HEIGHT, WORLD_WIDTH,
)
from src.entities.player import Entity
from src.systems.sprite_manager import sprite_manager

logger = logging.getLogger(__name__)


class Bot(Entity):
    """
    Bot adversário com IA baseada em FSM e avaliação de utilidade.

    Parâmetros:
        x, y                — posição inicial no mundo
        skin                — dicionário de skin (primary, secondary, accent)
        name                — nome exibido na HUD
        difficulty_profile  — DifficultyProfile ou string "facil"/"medio"/"dificil"

    Estados da FSM:
        evade       — fuga quando trilha própria está ameaçada (maior prioridade)
        return      — retorno ao território quando trilha está longa
        collect_pu  — desvio para coletar power-up próximo lucrativo
        intercept   — interceptação preditiva da trajetória inimiga
        hunt        — corte direto da trilha inimiga
        expand      — exploração e captura estratégica de território (padrão)

    Atributos públicos relevantes:
        state       — estado atual da FSM (string)
        difficulty  — valor numérico 0.0–2.0 derivado do perfil
        bot_effects — dict de efeitos de power-up ativos {tipo: ActiveEffect}
    """

    # Prioridade de tipos de power-up por estado (sobrescrita pelo perfil)
    _DEFAULT_PU_PRIORITY = {
        "expand":     ["BOMB", "SPEED", "SIZE_UP", "SHIELD", "EAGLE"],
        "hunt":       ["SPEED", "SIZE_UP", "BOMB",  "SHIELD", "EAGLE"],
        "intercept":  ["SPEED", "BOMB",   "SIZE_UP","SHIELD", "EAGLE"],
        "evade":      ["SHIELD","SPEED",  "EAGLE",  "BOMB",   "SIZE_UP"],
        "return":     ["SHIELD","SPEED",  "EAGLE",  "BOMB",   "SIZE_UP"],
        "collect_pu": ["BOMB",  "SPEED",  "SIZE_UP","SHIELD", "EAGLE"],
    }

    def __init__(
        self,
        x: float,
        y: float,
        skin: dict,
        name: str = "",
        difficulty_profile: DifficultyProfile | str = DEFAULT_DIFFICULTY,
    ) -> None:
        # Resolve perfil (aceita string ou objeto)
        if isinstance(difficulty_profile, str):
            self._profile = get_profile(difficulty_profile)
        else:
            self._profile = difficulty_profile

        speed = BOT_SPEED_BASE * self._profile.speed_multiplier
        super().__init__(
            x, y,
            self._profile.name,   # nome do perfil não sobrescreve o nome do bot
            speed,
            name=name or "Bot",
            secondary=skin["secondary"],
            accent=skin["accent"],
        )
        # Sobrescreve a cor principal com a skin
        self.color = skin["primary"]

        # Valor numérico legado (usado em alguns cálculos internos)
        self.difficulty = self._profile.speed_multiplier

        self._think_timer    = random.uniform(0, self._profile.think_interval)
        self.state           = "expand"
        self._wander_steps   = 0
        self._last_pos       = (x, y)
        self._stuck_timer    = 0.0
        self._pu_target: Optional[Any] = None
        self.bot_effects: dict = {}     # efeitos de power-up ativos

    # -----------------------------------------------------------------------
    # Propriedade de perfil
    # -----------------------------------------------------------------------

    @property
    def profile(self) -> DifficultyProfile:
        """Perfil de dificuldade imutável associado a este bot."""
        return self._profile

    # -----------------------------------------------------------------------
    # Ciclo de IA principal
    # -----------------------------------------------------------------------

    def update_ai(
        self,
        dt: float,
        world,
        entities: List[Entity],
        powerup_items: Optional[List] = None,
    ) -> None:
        """
        Avalia o estado da FSM e executa a ação correspondente.

        A reavaliação ocorre a cada `think_interval` segundos (definido
        pelo DifficultyProfile). Entre reavaliações, o bot segue na
        direção já definida — isso evita oscilação e reduz custo computacional.

        Parâmetros:
            dt            — delta time em segundos
            world         — instância de World (leitura de território)
            entities      — todas as entidades vivas (Player + Bots)
            powerup_items — lista de PowerUpItem disponíveis no mapa
        """
        if not self.alive:
            return

        self._think_timer -= dt
        if self._think_timer > 0:
            return
        self._think_timer = self._profile.think_interval

        # Anti-stuck: força guinada se o bot não se moveu
        dx = self.x - self._last_pos[0]
        dy = self.y - self._last_pos[1]
        if math.hypot(dx, dy) < 2.0:
            self._stuck_timer += self._profile.think_interval
            if self._stuck_timer > 1.5:
                self._force_unstick(world)
                self._stuck_timer = 0.0
        else:
            self._stuck_timer = 0.0
        self._last_pos = (self.x, self.y)

        trail_len = len(self.trail.points)
        own       = world.is_own_territory(self.x, self.y, self.id)

        # ── Prioridade 1: Evade (sobrevivência) ──────────────────────────────
        if self._assess_danger(entities) and trail_len > 6:
            self.state = "evade"
            self._do_evade(world, entities)
            return

        # ── Prioridade 2: Return (trilha longa) ──────────────────────────────
        max_trail = int(16 + 32 * self._profile.max_trail_factor)
        if not own and trail_len > max_trail:
            self.state = "return"
            self._do_return(world)
            return

        # ── Prioridade 3: Collect power-up ───────────────────────────────────
        if powerup_items:
            best_pu = self._best_powerup(powerup_items, entities)
            if best_pu is not None:
                self._pu_target = best_pu
                self.state = "collect_pu"
                self._steer_to(best_pu.x, best_pu.y)
                return
        self._pu_target = None

        # ── Prioridade 4: Intercept ───────────────────────────────────────────
        if random.random() < self._profile.intercept_prob:
            pt = self._find_intercept(entities)
            if pt is not None:
                self.state = "intercept"
                self._steer_to(*pt)
                return

        # ── Prioridade 5: Hunt ────────────────────────────────────────────────
        if random.random() < self._profile.hunt_prob:
            pt = self._find_hunt_target(entities)
            if pt is not None:
                self.state = "hunt"
                self._steer_to(*pt)
                return

        # ── Prioridade 6: Expand (padrão) ────────────────────────────────────
        self.state = "expand"
        self._do_expand(world)

    # -----------------------------------------------------------------------
    # Comportamentos por estado
    # -----------------------------------------------------------------------

    def _do_expand(self, world) -> None:
        """
        Captura território de forma estratégica.

        Avança na direção atual por `patience` avaliações antes de redirecionar.
        A probabilidade de mudança espontânea é inversamente proporcional ao
        fator de trilha máxima (bots mais cautelosos mudam menos de direção).
        """
        self._wander_steps += 1
        patience  = int(6 + 12 * self._profile.max_trail_factor)
        turn_prob = max(0.04, 0.28 - 0.10 * self._profile.max_trail_factor)
        if self._wander_steps >= patience or random.random() < turn_prob:
            self._strategic_turn(world)
            self._wander_steps = 0

    def _do_return(self, world) -> None:
        """
        Retorna ao território pelo caminho mais curto.

        Usa busca lookahead em 4 direções candidatas, penalizando bordas
        e preferindo caminhos que cruzem o próprio território rapidamente.
        """
        best = self._best_direction_toward_own(world, lookahead=20)
        if best:
            self.set_direction(*best)
        else:
            self._strategic_turn(world)

    def _do_evade(self, world, entities: List[Entity]) -> None:
        """
        Foge para o próprio território desviando da ameaça mais próxima.

        Combina a direção de fuga (oposta ao inimigo) com a direção para
        casa. Se as duas forem compatíveis, prioriza o retorno ao território.
        """
        threat_dir = self._threat_direction(entities)
        home_dir   = self._best_direction_toward_own(world, lookahead=12)
        if home_dir and threat_dir:
            if home_dir != (-threat_dir[0], -threat_dir[1]):
                self.set_direction(*home_dir)
            else:
                self.set_direction(*threat_dir)
        elif home_dir:
            self.set_direction(*home_dir)
        elif threat_dir:
            self.set_direction(*threat_dir)

    # -----------------------------------------------------------------------
    # Avaliação de power-ups
    # -----------------------------------------------------------------------

    def _best_powerup(
        self, items: List, entities: List[Entity]
    ) -> Optional[Any]:
        """
        Seleciona o power-up com maior utilidade esperada.

        Função de pontuação:
            score = (1 - dist/max_dist) + rank_bonus - risco_trilha

        Onde rank_bonus favorece tipos prioritários do perfil de dificuldade
        e risco_trilha penaliza o desvio quando a trilha está exposta.

        Parâmetros:
            items    — lista de PowerUpItem disponíveis
            entities — usada para detectar perigo antes de desviar

        Retorna:
            PowerUpItem com maior score, ou None se nenhum for lucrativo.
        """
        trail_len = len(self.trail.points)
        # Não desviar em situação de perigo ou trilha muito longa
        if trail_len > 60 or self._assess_danger(entities):
            return None

        priority: List[str] = self._profile.priority_types or list(
            self._DEFAULT_PU_PRIORITY.get(self.state, [])
        )
        max_dist   = self._profile.powerup_max_dist
        best_score = 0.20          # score mínimo para considerar valer o desvio
        best_item  = None

        for item in items:
            dist = math.hypot(item.x - self.x, item.y - self.y)
            if dist > max_dist:
                continue

            # Pontuação base: proximidade normalizada
            score = 1.0 - (dist / max_dist)

            # Bônus por tipo prioritário
            if item.kind in priority:
                rank   = priority.index(item.kind)
                score += (len(priority) - rank) * 0.12

            # Penalidade por trilha exposta
            if trail_len > 15:
                score -= 0.25 * (trail_len / 60)

            if score > best_score:
                best_score = score
                best_item  = item

        return best_item

    # -----------------------------------------------------------------------
    # Busca de alvos
    # -----------------------------------------------------------------------

    def _find_hunt_target(
        self, entities: List[Entity]
    ) -> Optional[Tuple[float, float]]:
        """
        Localiza o ponto mais vulnerável de uma trilha inimiga.

        Alvo preferencial: meio da trilha (ponto mais difícil de defender,
        pois exige que o inimigo percorra toda a distância até o território).

        Retorna:
            Coordenadas do ponto alvo, ou None se não houver alvo adequado.
        """
        hunt_range = AI_HUNT_RANGE * self._profile.hunt_range_factor
        best_dist  = hunt_range
        best_pt: Optional[Tuple[float, float]] = None

        for e in entities:
            if e is self or not e.alive or not e.drawing:
                continue
            pts = e.trail.points
            if len(pts) < 8:
                continue
            mid   = len(pts) // 2
            chunk = pts[max(0, mid - 3): mid + 4]
            for pt in chunk:
                dist = math.hypot(pt[0] - self.x, pt[1] - self.y)
                if dist < best_dist:
                    best_dist = dist
                    best_pt   = pt

        return best_pt

    def _find_intercept(
        self, entities: List[Entity]
    ) -> Optional[Tuple[float, float]]:
        """
        Prevê a posição futura de um inimigo e mira à frente dele.

        Estratégia de interceptação:
            1. Para cada inimigo com trilha exposta, calcula a posição
               prevista em `lookahead_steps` passos de reavaliação.
            2. Pontua pela extensão da trilha (mais trilha = mais área
               a conquistar) e penaliza pela distância ao ponto previsto.

        Retorna:
            Coordenadas do ponto de interceptação ótimo, ou None.
        """
        hunt_range = AI_HUNT_RANGE * self._profile.hunt_range_factor * 1.4
        best_score = 0.0
        best_pt: Optional[Tuple[float, float]] = None
        look       = self._profile.lookahead_steps

        for e in entities:
            if e is self or not e.alive or not e.drawing:
                continue
            if len(e.trail.points) < 10:
                continue
            # Posição prevista
            step_dist = e.speed * self._profile.think_interval * look
            pred_x    = e.x + e.direction[0] * step_dist
            pred_y    = e.y + e.direction[1] * step_dist
            dist      = math.hypot(pred_x - self.x, pred_y - self.y)
            if dist > hunt_range:
                continue
            score = len(e.trail.points) / 60.0 - dist / hunt_range
            if score > best_score:
                best_score = score
                best_pt    = (pred_x, pred_y)

        return best_pt if best_score > 0.0 else None

    # -----------------------------------------------------------------------
    # Avaliação de perigo
    # -----------------------------------------------------------------------

    def _assess_danger(self, entities: List[Entity]) -> bool:
        """
        Verifica se algum inimigo está dentro do raio de perigo da trilha.

        Pontos da trilha verificados a cada 3 índices para reduzir custo.

        Retorna:
            True se pelo menos um inimigo estiver ameaçando a trilha.
        """
        pts         = self.trail.points
        danger_r    = AI_DANGER_RANGE * self._profile.danger_range_factor
        if len(pts) < 5:
            return False
        for e in entities:
            if e is self or not e.alive:
                continue
            for pt in pts[::3]:
                if math.hypot(e.x - pt[0], e.y - pt[1]) < danger_r:
                    return True
        return False

    def _threat_direction(
        self, entities: List[Entity]
    ) -> Optional[Tuple[int, int]]:
        """
        Calcula a direção de fuga em relação ao inimigo mais próximo.

        Retorna:
            Tupla de direção (dx, dy) ou None se não houver inimigo.
        """
        nearest_dist = 9_999.0
        nearest: Optional[Entity] = None
        for e in entities:
            if e is self or not e.alive:
                continue
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < nearest_dist:
                nearest_dist = d
                nearest      = e
        if nearest is None:
            return None
        dx, dy = self.x - nearest.x, self.y - nearest.y
        return (1 if dx > 0 else -1, 0) if abs(dx) >= abs(dy) \
            else (0, 1 if dy > 0 else -1)

    # -----------------------------------------------------------------------
    # Navegação
    # -----------------------------------------------------------------------

    def _steer_to(self, tx: float, ty: float) -> None:
        """
        Define a melhor direção em 90° para alcançar o ponto (tx, ty).

        Usa produto interno (dot product) para escolher entre as direções
        candidatas (excluindo reversão de 180°).

        Parâmetros:
            tx, ty — coordenadas do alvo no mundo
        """
        dx, dy   = tx - self.x, ty - self.y
        length   = math.hypot(dx, dy) or 1.0
        nx, ny   = dx / length, dy / length
        candidates = [
            d for d in DIRECTIONS
            if d != (-self.direction[0], -self.direction[1])
        ]
        best_dir = max(candidates, key=lambda d: d[0] * nx + d[1] * ny)
        self.set_direction(*best_dir)

    def _strategic_turn(self, world) -> None:
        """
        Avalia cada direção candidata por uma função de pontuação multi-critério.

        Critérios (em ordem de peso):
            1. Células sem dono à frente (+0.5 / step, decaimento por distância)
            2. Células inimigas (+0.3 / step, captura oportunista)
            3. Células próprias (-0.1 / step, evita entrar no próprio território)
            4. Proximidade de borda (-0.6, penalidade de risco)
            5. Ruído aleatório leve (evita comportamento determinístico)

        Parâmetros:
            world — instância de World para consulta de ownership
        """
        candidates = [
            d for d in DIRECTIONS
            if d != (-self.direction[0], -self.direction[1])
        ]
        scored = []
        for d in candidates:
            score = random.uniform(0.0, 0.08)
            px, py = self.x, self.y
            for step in range(1, 7):
                px += d[0] * CELL_SIZE * step
                py += d[1] * CELL_SIZE * step
                owner = world.get_owner(px, py)
                if owner == 0:
                    score += 0.50 / step
                elif owner != self.id:
                    score += 0.30 / step
                else:
                    score -= 0.10 / step
            if not world.is_playable_point(px, py):
                score -= 0.60
            scored.append((score, d))
        scored.sort(key=lambda t: t[0], reverse=True)
        self.set_direction(*scored[0][1])

    def _best_direction_toward_own(
        self, world, lookahead: int = 20
    ) -> Optional[Tuple[int, int]]:
        """
        Encontra a direção que leva ao próprio território mais rapidamente.

        Realiza busca em linha reta em cada direção candidata por até
        `lookahead` passos de tamanho CELL_SIZE * 2.

        Parâmetros:
            world     — instância de World
            lookahead — número máximo de passos de busca

        Retorna:
            Tupla (dx, dy) da melhor direção, ou None se não encontrar.
        """
        candidates = [
            d for d in DIRECTIONS
            if d != (-self.direction[0], -self.direction[1])
        ]
        best_dir, best_steps = None, lookahead + 1
        step_size = CELL_SIZE * 2

        for d in candidates:
            px, py = self.x, self.y
            for step in range(1, lookahead + 1):
                px += d[0] * step_size
                py += d[1] * step_size
                if not world.is_playable_point(px, py):
                    break
                if world.is_own_territory(px, py, self.id) and step < best_steps:
                    best_steps = step
                    best_dir   = d
                    break

        return best_dir

    def _force_unstick(self, world) -> None:
        """
        Mecanismo anti-stuck: força direção perpendicular quando o bot
        permanece imóvel por mais de 1.5 s.

        Tenta primeiro as direções perpendiculares à atual;
        fallback: direção aleatória não reversa.
        """
        perp = [
            (-self.direction[1],  self.direction[0]),
            ( self.direction[1], -self.direction[0]),
        ]
        random.shuffle(perp)
        for d in perp:
            px = self.x + d[0] * 30
            py = self.y + d[1] * 30
            if world.is_playable_point(px, py):
                self.set_direction(*d)
                return
        candidates = [
            d for d in DIRECTIONS
            if d != (-self.direction[0], -self.direction[1])
        ]
        self.set_direction(*random.choice(candidates))
        logger.debug("Bot '%s' anti-stuck ativado.", self.name)

    # -----------------------------------------------------------------------
    # Alias para trilha (usado em avaliações internas)
    # -----------------------------------------------------------------------

    @property
    def trail_set(self) -> set:
        """Conjunto de células (cx, cy) da trilha atual."""
        return {
            (int(p[0]) // CELL_SIZE, int(p[1]) // CELL_SIZE)
            for p in self.trail.points
        }

    # -----------------------------------------------------------------------
    # Renderização
    # -----------------------------------------------------------------------

    def draw(self, surface: pygame.Surface,
             camera_offset: Tuple[float, float]) -> None:
        """
        Renderiza o bot na superfície com offset de câmera.

        Usa sprite configurado em sprites.json ou fallback procedural.
        Exibe indicador visual de estado (ponto colorido acima do bot).

        Parâmetros:
            surface       — pygame.Surface de destino
            camera_offset — tupla (ox, oy) do offset da câmera
        """
        ox, oy = camera_offset

        # Trilha com cor modificada por estado
        if len(self.trail.points) >= 2 and (self.alive or self.death_timer > 0):
            pts = [(int(p[0] - ox), int(p[1] - oy)) for p in self.trail.points]
            pygame.draw.lines(surface, self.secondary, False, pts, TRAIL_WIDTH + 4)
            trail_col = self._trail_color_by_state()
            pygame.draw.lines(surface, trail_col, False, pts, TRAIL_WIDTH)
            core = tuple(min(255, c + 50) for c in trail_col)
            pygame.draw.lines(surface, core, False, pts, max(1, TRAIL_WIDTH - 2))

        if not self.alive:
            return

        sx = int(self.x - ox)
        sy = int(self.y - oy)
        r  = PLAYER_RADIUS

        sprite     = sprite_manager.get("bot.default")
        use_sprite = sprite.get_width() > 2

        if use_sprite:
            diam   = r * 2 + 6
            scaled = sprite_manager.get_scaled("bot.default", diam, diam)
            surface.blit(scaled, (sx - diam // 2, sy - diam // 2))
        else:
            gr    = r + 6
            gsurf = pygame.Surface((gr * 2 + 2, gr * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(gsurf, (*self.color[:3], 50), (gr + 1, gr + 1), gr)
            surface.blit(gsurf, (sx - gr - 1, sy - gr - 1),
                         special_flags=pygame.BLEND_ALPHA_SDL2)
            pygame.draw.circle(surface, self.secondary, (sx, sy), r + 3)
            pygame.draw.circle(surface, self.color,     (sx, sy), r)
            pygame.draw.circle(surface, self.accent,    (sx, sy), r,     2)
            pygame.draw.circle(surface, self.accent,    (sx - 2, sy - 2), 3)

        # Indicador de estado (ponto colorido)
        state_colors = {
            "hunt":       (255,  60,  60),
            "intercept":  (255, 120,   0),
            "evade":      (255, 220,   0),
            "collect_pu": (100, 255, 200),
            "return":     (100, 200, 255),
            "expand":     (180, 180, 180),
        }
        sc = state_colors.get(self.state, (200, 200, 200))
        pygame.draw.circle(surface, sc, (sx, sy - r - 5), 3)

        # Indicador de direção
        dx, dy = self.direction
        pygame.draw.circle(surface, (255, 255, 255),
                           (sx + int(dx * 5), sy + int(dy * 5)), 3)
        self.draw_name_tag(surface, sx, sy, r, extra_lift=6)

    def _trail_color_by_state(self) -> Tuple[int, int, int]:
        """Retorna cor da trilha levemente modificada pelo estado atual."""
        c = self.color
        if self.state == "hunt":
            return (min(255, c[0] + 40), max(0, c[1] - 20), max(0, c[2] - 20))
        if self.state == "intercept":
            return (min(255, c[0] + 30), min(255, c[1] + 10), max(0, c[2] - 10))
        if self.state == "evade":
            return (min(255, c[0] + 20), min(255, c[1] + 20), max(0, c[2] - 20))
        return c
