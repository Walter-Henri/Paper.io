"""
difficulty.py — TerritórIO: Edição Brasil
------------------------------------------
Responsabilidade:
    Definir os perfis de dificuldade dos bots de forma centralizada e
    configurável. Cada perfil ajusta parâmetros de IA sem alterar a
    velocidade de forma artificial — a diferença está na qualidade das
    decisões, não na vantagem numérica de velocidade.

Uso:
    from src.config.difficulty import DifficultyProfile, DIFFICULTIES
    profile = DIFFICULTIES["medio"]
    bot = Bot(x, y, skin, difficulty_profile=profile)

Para adicionar um novo nível:
    Inclua uma nova entrada no dicionário DIFFICULTIES abaixo.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class DifficultyProfile:
    """
    Perfil imutável de dificuldade de um bot.

    Atributos:
        name                — nome exibível do nível
        speed_multiplier    — multiplicador sobre BOT_SPEED_BASE (1.0 = base)
        think_interval      — intervalo de reavaliação de IA em segundos
                              (menor = reage mais rápido)
        hunt_range_factor   — fator sobre AI_HUNT_RANGE (1.0 = base)
        danger_range_factor — fator sobre AI_DANGER_RANGE
        max_trail_factor    — fração da trilha máxima antes de retornar
                              (menor = retorna mais cedo = mais cauteloso)
        intercept_prob      — probabilidade de usar interceptação por frame
        hunt_prob           — probabilidade de usar caça por frame
        powerup_max_dist    — distância máxima para desviar por power-up (px)
        lookahead_steps     — quantos passos prever na interceptação
        priority_types      — tipos de power-up preferidos (ordem decrescente)
    """
    name:                str
    speed_multiplier:    float
    think_interval:      float
    hunt_range_factor:   float
    danger_range_factor: float
    max_trail_factor:    float
    intercept_prob:      float
    hunt_prob:           float
    powerup_max_dist:    float
    lookahead_steps:     int
    priority_types:      List[str] = field(default_factory=list)


#
# Perfis de dificuldade
#
DIFFICULTIES: dict[str, DifficultyProfile] = {

    # Fácil
    # O bot prioriza expansão simples, retorna cedo ao território,
    # raramente persegue e tem baixa frequência de reavaliação.
    # Adequado para jogadores iniciantes aprenderem as mecânicas.
    "facil": DifficultyProfile(
        name                = "Fácil",
        speed_multiplier    = 0.82,
        think_interval      = 0.55,      # pensa menos de 2× por segundo
        hunt_range_factor   = 0.55,      # alcance de caça reduzido
        danger_range_factor = 0.70,
        max_trail_factor    = 0.55,      # retorna cedo (trilha curta)
        intercept_prob      = 0.08,      # raramente intercepta
        hunt_prob           = 0.12,
        powerup_max_dist    = 110.0,
        lookahead_steps     = 1,
        priority_types      = ["SHIELD", "SPEED", "SIZE_UP", "BOMB", "EAGLE"],
    ),

    # Médio
    # Equilíbrio entre expansão e agressividade.
    # Avalia oportunidades e riscos de forma razoável.
    # Dificuldade padrão da partida.
    "medio": DifficultyProfile(
        name                = "Médio",
        speed_multiplier    = 0.95,
        think_interval      = 0.32,
        hunt_range_factor   = 0.85,
        danger_range_factor = 0.90,
        max_trail_factor    = 0.72,
        intercept_prob      = 0.22,
        hunt_prob           = 0.28,
        powerup_max_dist    = 180.0,
        lookahead_steps     = 2,
        priority_types      = ["BOMB", "SPEED", "SIZE_UP", "SHIELD", "EAGLE"],
    ),

    # Difícil
    # Alta frequência de reavaliação, maior alcance de detecção,
    # interceptação agressiva e uso estratégico de power-ups.
    # Desafiador para jogadores experientes.
    "dificil": DifficultyProfile(
        name                = "Difícil",
        speed_multiplier    = 1.08,
        think_interval      = 0.14,      # reage cerca de 7× por segundo
        hunt_range_factor   = 1.20,
        danger_range_factor = 1.15,
        max_trail_factor    = 0.88,      # aceita trilhas mais longas
        intercept_prob      = 0.40,
        hunt_prob           = 0.45,
        powerup_max_dist    = 260.0,
        lookahead_steps     = 4,
        priority_types      = ["SPEED", "BOMB", "SIZE_UP", "SHIELD", "EAGLE"],
    ),
}

# Perfil padrão usado quando nenhum é especificado
DEFAULT_DIFFICULTY = "medio"


def get_profile(name: str) -> DifficultyProfile:
    """
    Retorna o perfil de dificuldade pelo nome.

    Parâmetros:
        name — "facil", "medio" ou "dificil" (case-insensitive)

    Retorna:
        DifficultyProfile correspondente, ou perfil médio como fallback.
    """
    return DIFFICULTIES.get(name.lower(), DIFFICULTIES[DEFAULT_DIFFICULTY])


_TIERS = ("facil", "medio", "dificil")


def promote_tier(name: str, level: int) -> str:
    """Sobe o tier base a cada 2 fases (teto: difícil)."""
    promo = min(2, max(0, level - 1) // 2)
    try:
        idx = _TIERS.index(name.lower())
    except ValueError:
        idx = 1
    return _TIERS[min(2, idx + promo)]


def evolve_for_level(profile: DifficultyProfile, level: int) -> DifficultyProfile:
    """
    Afia o perfil conforme a fase. Nível 1 = perfil base.
    Cada fase seguinte deixa o bot mais rápido para decidir, mais agressivo
    e com mais alcance, com teto para não explodir os números.
    """
    steps = max(0, int(level) - 1)
    if steps == 0:
        return profile
    return DifficultyProfile(
        name=profile.name,
        speed_multiplier=min(1.25, profile.speed_multiplier + 0.02 * steps),
        think_interval=max(0.07, profile.think_interval * (0.92 ** steps)),
        hunt_range_factor=min(1.85, profile.hunt_range_factor + 0.05 * steps),
        danger_range_factor=min(1.70, profile.danger_range_factor + 0.04 * steps),
        max_trail_factor=min(0.95, profile.max_trail_factor + 0.02 * steps),
        intercept_prob=min(0.75, profile.intercept_prob + 0.035 * steps),
        hunt_prob=min(0.80, profile.hunt_prob + 0.035 * steps),
        powerup_max_dist=min(420.0, profile.powerup_max_dist + 18.0 * steps),
        lookahead_steps=min(8, profile.lookahead_steps + steps // 2),
        priority_types=list(profile.priority_types),
    )
