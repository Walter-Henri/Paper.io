"""
collision.py — TerritórIO: Edição Brasil
-----------------------------------------
Responsabilidade:
    Detectar colisões entre a cabeça de cada entidade e os segmentos
    de trilha das demais entidades no mapa.

Regras de eliminação:
    - Nenhuma entidade (jogador ou bot) morre pela PRÓPRIA trilha.
      Autocolisão é completamente ignorada para todos.
    - Uma entidade morre ao tocar a trilha de OUTRA entidade.
    - O escudo ativo protege o JOGADOR de morrer por trilha alheia.

Retorna lista de pares (killer, victim) sem duplicatas de vítima.
Não aplica as mortes diretamente — isso é responsabilidade de game.py.

Correção v1.3.2:
    Autocolisão removida também para bots (antes era parcialmente
    mantida via MIN_SELF_TRAIL / SELF_IMMUNITY_POINTS, o que causava
    eliminação incorreta ao atravessar a própria trilha).
"""

from __future__ import annotations

import math
from typing import List, Tuple

from src.config.game_config import KILL_RADIUS
from src.entities.player import Entity


def _point_to_segment_dist(px: float, py: float,
                            ax: float, ay: float,
                            bx: float, by: float) -> float:
    """
    Distância mínima entre o ponto (px, py) e o segmento (ax,ay)→(bx,by).

    Parâmetros:
        px, py — coordenadas do ponto
        ax, ay — extremo inicial do segmento
        bx, by — extremo final do segmento

    Retorna:
        Distância em pixels (float ≥ 0).
    """
    abx, aby = bx - ax, by - ay
    apx, apy = px - ax, py - ay
    ab_len2  = abx * abx + aby * aby
    if ab_len2 < 1e-6:
        return math.hypot(apx, apy)
    t = max(0.0, min(1.0, (apx * abx + apy * aby) / ab_len2))
    return math.hypot(px - (ax + t * abx), py - (ay + t * aby))


def check_collisions(
    entities: List[Entity],
    player_entity: Entity,
    shield_active: bool,
) -> List[Tuple[Entity, Entity]]:
    """
    Verifica colisões trilha→cabeça entre todas as entidades vivas.

    Regras implementadas:
        1. Autocolisão ignorada para TODOS (jogador e bots).
           Nenhuma entidade morre ao atravessar a própria trilha.
        2. Colisão com trilha ALHEIA elimina a entidade colidindo.
        3. Escudo ativo protege apenas o jogador de trilhas inimigas.

    Parâmetros:
        entities      — lista de todas as entidades (Player + Bots)
        player_entity — referência ao jogador humano
        shield_active — True se o escudo do jogador está ativo

    Retorna:
        Lista de pares (killer, victim) sem vítimas duplicadas.
        'killer' é quem possui a trilha que causou a eliminação.
        'victim' é quem colidiu com essa trilha.
    """
    kills  = []
    radius = KILL_RADIUS

    for head in entities:
        if not head.alive:
            continue
        hx, hy = head.x, head.y

        for trail_owner in entities:
            if not trail_owner.alive or not trail_owner.trail.active:
                continue

            # ── REGRA 1: autocolisão ignorada para todos ──────────────────
            if trail_owner is head:
                continue

            points = trail_owner.trail.points
            if len(points) < 2:
                continue

            # Verifica cada segmento da trilha alheia
            hit = False
            for i in range(1, len(points)):
                ax, ay = points[i - 1]
                bx, by = points[i]
                if _point_to_segment_dist(hx, hy, ax, ay, bx, by) < radius:
                    hit = True
                    break

            if not hit:
                continue

            # ── REGRA 2: escudo protege o jogador ────────────────────────
            if head is player_entity and shield_active:
                break   # protegido — ignora todos os hits desta iteração

            kills.append((head, trail_owner))
            break   # uma colisão por cabeça é suficiente

    # Remove duplicatas de vítimas (cada entidade morre no máximo uma vez)
    seen:   set  = set()
    unique: list = []
    for killer, victim in kills:
        if victim.id not in seen:
            seen.add(victim.id)
            unique.append((killer, victim))
    return unique
