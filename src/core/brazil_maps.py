# Responsabilidade:
# Carregar o contorno real de cada estado brasileiro e projetá-lo
# na arena (pixels do mundo), corrigindo a escala leste-oeste.
# Não contém lógica de jogo, colisão ou comportamento de entidades.

from __future__ import annotations

import json
import math
import os
from typing import List, Tuple

from src.config.game_config import WORLD_WIDTH, WORLD_HEIGHT

Point = Tuple[float, float]

_DATA = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "assets", "data", "state_outlines.json")
)

def _load_outlines() -> dict[str, List[Point]]:
    try:
        with open(_DATA, encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return {}
    outlines: dict[str, List[Point]] = {}
    for name, ring in raw.items():
        outlines[name] = [(float(p[0]), float(p[1])) for p in ring]
    return outlines


# Contornos (lon, lat), anel principal de cada estado, simplificados.
STATES: dict[str, List[Point]] = _load_outlines()

# Ordem de progressão por nível
STATE_ORDER: List[str] = [
    "São Paulo", "Rio de Janeiro", "Minas Gerais", "Bahia", "Rio Grande do Sul",
    "Paraná", "Santa Catarina", "Pernambuco", "Ceará", "Goiás",
    "Pará", "Maranhão", "Amazonas", "Mato Grosso", "Mato Grosso do Sul",
    "Rio Grande do Norte", "Paraíba", "Espírito Santo", "Piauí", "Alagoas",
    "Rondônia", "Tocantins", "Sergipe", "Amapá", "Roraima", "Acre", "Distrito Federal",
]


def get_state_polygon(name: str) -> List[Point]:
    return STATES.get(name, [])


def project_polygon(polygon: List[Point],
                    screen_w: int, screen_h: int,
                    margin: int = 48) -> List[Tuple[float, float]]:
    """
    Projeta (lon, lat) em pixels. O grau de longitude é comprimido
    por cos(latitude) para o contorno não ficar esticado.
    """
    if not polygon:
        return []
    lons = [p[0] for p in polygon]
    lats = [p[1] for p in polygon]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    mid = math.radians((min_lat + max_lat) / 2.0)
    kx = max(0.25, math.cos(mid))
    span_x = (max_lon - min_lon) * kx or 1.0
    span_y = (max_lat - min_lat) or 1.0
    uw = screen_w - 2 * margin
    uh = screen_h - 2 * margin
    scale = min(uw / span_x, uh / span_y)
    ox = margin + (uw - span_x * scale) / 2.0
    oy = margin + (uh - span_y * scale) / 2.0
    return [
        (ox + (lon - min_lon) * kx * scale,
         oy + (max_lat - lat) * scale)
        for lon, lat in polygon
    ]


def state_arena_polygon(name: str,
                        world_w: int = WORLD_WIDTH,
                        world_h: int = WORLD_HEIGHT,
                        margin: int = 8) -> List[Tuple[float, float]]:
    """Contorno do estado em pixels, no maior tamanho que cabe na arena."""
    return project_polygon(get_state_polygon(name), world_w, world_h, margin)


def point_in_polygon(px: float, py: float,
                     poly: List[Tuple[float, float]]) -> bool:
    """Ray-casting. Aceita polígono aberto ou fechado."""
    n = len(poly)
    if n < 3:
        return False
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > py) != (yj > py)) and \
           (px < (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi):
            inside = not inside
        j = i
    return inside
