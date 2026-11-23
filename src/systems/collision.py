# Responsabilidade:
# Detectar colisões entre cabeças de entidades e trilhas.
# Implementa proteção contra autocolisão do jogador e respeita o escudo.
# Retorna pares (killer, victim) sem aplicar as mortes diretamente.
# Não contém lógica de movimento, renderização ou IA.

from __future__ import annotations
from typing import List, Tuple
import math

from src.entities.player  import Entity
from src.config.game_config import (
    KILL_RADIUS, SELF_IMMUNITY_POINTS, MIN_SELF_TRAIL
)


def _point_to_segment_dist(px: float, py: float,
                            ax: float, ay: float,
                            bx: float, by: float) -> float:
    abx, aby  = bx - ax, by - ay
    apx, apy  = px - ax, py - ay
    ab_len2   = abx * abx + aby * aby
    if ab_len2 < 1e-6:
        return math.hypot(apx, apy)
    t = max(0.0, min(1.0, (apx * abx + apy * aby) / ab_len2))
    return math.hypot(px - (ax + t * abx), py - (ay + t * aby))


def check_collisions(entities: List[Entity],
                     player_entity: Entity,
                     shield_active: bool) -> List[Tuple[Entity, Entity]]:
    """
    Detecta colisões trilha→cabeça com duas regras adicionais:
    1. Jogador nunca morre pela própria trilha (autocolisão removida).
    2. Escudo ativo protege o jogador de trilhas inimigas.

    Retorna lista de pares (killer, victim) sem duplicatas de vítima.
    """
    kills  = []
    radius = KILL_RADIUS

    for head in entities:
        if not head.alive:
            continue
        hx, hy = head.x, head.y

        for victim in entities:
            if not victim.alive or not victim.trail.active:
                continue
            points = victim.trail.points
            n      = len(points)
            if n < 3:
                continue

            is_self = (victim is head)

            # ── Regra: jogador não morre pela própria trilha ────────────────
            if is_self and head is player_entity:
                continue

            # Bots mantêm autocolisão com imunidade parcial
            if is_self:
                if n < MIN_SELF_TRAIL:
                    continue
                end_idx = n - SELF_IMMUNITY_POINTS
                if end_idx < 2:
                    continue
                check_range = range(1, end_idx)
            else:
                check_range = range(1, n)

            hit = False
            for i in check_range:
                ax, ay = points[i - 1]
                bx, by = points[i]
                if _point_to_segment_dist(hx, hy, ax, ay, bx, by) < radius:
                    hit = True
                    break

            if hit:
                # ── Regra: escudo protege o jogador ────────────────────────
                if head is player_entity and not is_self and shield_active:
                    break
                kills.append((head, victim))
                break

    # Remove duplicatas de vítimas
    seen, unique = set(), []
    for killer, victim in kills:
        if victim.id not in seen:
            seen.add(victim.id)
            unique.append((killer, victim))
    return unique
