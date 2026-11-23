"""
test_collision.py — TerritórIO: Edição Brasil
-----------------------------------------------
Testes para src/systems/collision.py.

Cobre:
    - Distância ponto-segmento
    - Colisão cabeça × trilha inimiga
    - Autocolisão do jogador (removida — deve ser ignorada)
    - Proteção do escudo
    - Imunidade parcial dos bots na própria trilha

Execute com:
    python -m pytest tests/test_collision.py -v
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from src.systems.collision import _point_to_segment_dist, check_collisions
from src.entities.trail   import Trail
from src.config.game_config import KILL_RADIUS, MIN_SELF_TRAIL


# ---------------------------------------------------------------------------
# Helpers — entidades mínimas para testes
# ---------------------------------------------------------------------------

class _FakeTrail:
    """Trail mínima para injetar pontos em testes."""
    def __init__(self, points, active=True):
        self.points = points
        self.active = active


class _FakeEntity:
    """Entidade mínima sem inicialização de Pygame."""
    _counter = 0

    def __init__(self, x, y, points=None, alive=True, drawing=True):
        _FakeEntity._counter += 1
        self.id         = _FakeEntity._counter
        self.x          = float(x)
        self.y          = float(y)
        self.alive      = alive
        self.drawing    = drawing
        self.direction  = (1, 0)
        self.speed      = 100.0
        self.trail      = _FakeTrail(points or [])
        self.death_timer = 0.0
        self.color      = (100, 100, 200)

    def kill(self): self.alive = False


# ---------------------------------------------------------------------------
# _point_to_segment_dist
# ---------------------------------------------------------------------------

class TestPointToSegmentDist:
    def test_point_on_segment(self):
        """Ponto exatamente sobre o segmento → distância 0."""
        d = _point_to_segment_dist(5.0, 0.0, 0.0, 0.0, 10.0, 0.0)
        assert d == pytest.approx(0.0, abs=1e-6)

    def test_point_off_segment(self):
        """Ponto perpendicular ao meio do segmento → distância igual ao afastamento."""
        d = _point_to_segment_dist(5.0, 3.0, 0.0, 0.0, 10.0, 0.0)
        assert d == pytest.approx(3.0, abs=1e-6)

    def test_point_beyond_end(self):
        """Ponto além do extremo → distância ao extremo mais próximo."""
        d = _point_to_segment_dist(15.0, 0.0, 0.0, 0.0, 10.0, 0.0)
        assert d == pytest.approx(5.0, abs=1e-6)

    def test_degenerate_segment(self):
        """Segmento de comprimento zero → distância ao ponto único."""
        d = _point_to_segment_dist(3.0, 4.0, 0.0, 0.0, 0.0, 0.0)
        assert d == pytest.approx(5.0, abs=1e-6)


# ---------------------------------------------------------------------------
# check_collisions — colisão básica
# ---------------------------------------------------------------------------

class TestCheckCollisions:

    def _make_long_trail(self, start_x, y, n=MIN_SELF_TRAIL + 5):
        """Cria trilha horizontal com n pontos separados por 10px."""
        return [(start_x + i * 10, y) for i in range(n)]

    def test_head_on_enemy_trail_detected(self):
        """
        Cabeça do bot1 sobre a trilha do bot2 → deve gerar kill (bot2, bot2).
        """
        trail_pts = self._make_long_trail(0, 100)
        head_x    = trail_pts[len(trail_pts) // 2][0]   # meio da trilha
        head_y    = 100.0

        player = _FakeEntity(999, 999)   # jogador longe
        bot1   = _FakeEntity(head_x, head_y)
        bot2   = _FakeEntity(0, 999, points=trail_pts)

        entities = [player, bot1, bot2]
        kills    = check_collisions(entities, player, shield_active=False)
        victims  = [v.id for _, v in kills]
        assert bot2.id in victims

    def test_player_self_trail_ignored(self):
        """
        Jogador sobre a própria trilha → NÃO deve ser eliminado.
        (autocolisão removida por design)
        """
        trail_pts = self._make_long_trail(0, 50)
        player    = _FakeEntity(trail_pts[5][0], 50.0, points=trail_pts)
        entities  = [player]
        kills     = check_collisions(entities, player, shield_active=False)
        assert all(v is not player for _, v in kills)

    def test_shield_protects_player(self):
        """
        Jogador com escudo sobre trilha inimiga → não deve ser eliminado.
        """
        trail_pts = self._make_long_trail(0, 200)
        player    = _FakeEntity(trail_pts[5][0], 200.0)
        enemy     = _FakeEntity(999, 999, points=trail_pts)
        entities  = [player, enemy]
        kills     = check_collisions(entities, player, shield_active=True)
        assert all(v is not player for _, v in kills)

    def test_no_shield_player_dies(self):
        """
        Jogador sem escudo sobre trilha inimiga → deve ser eliminado.
        """
        trail_pts = self._make_long_trail(0, 300)
        head_x    = trail_pts[len(trail_pts) // 2][0]
        player    = _FakeEntity(head_x, 300.0)
        enemy     = _FakeEntity(9999, 9999, points=trail_pts)
        entities  = [player, enemy]
        kills     = check_collisions(entities, player, shield_active=False)
        victims   = [v.id for _, v in kills]
        assert player.id in victims

    def test_dead_entity_not_checked(self):
        """Entidades com alive=False não devem ser verificadas."""
        trail_pts = self._make_long_trail(0, 400)
        head_x    = trail_pts[5][0]
        player    = _FakeEntity(999, 999)
        dead_bot  = _FakeEntity(head_x, 400.0, alive=False)
        enemy     = _FakeEntity(0, 999, points=trail_pts)
        entities  = [player, dead_bot, enemy]
        kills     = check_collisions(entities, player, shield_active=False)
        assert all(k is not dead_bot and v is not dead_bot for k, v in kills)

    def test_no_duplicate_victims(self):
        """Cada vítima deve aparecer no máximo uma vez na lista de kills."""
        trail_pts = self._make_long_trail(0, 500)
        head_x    = trail_pts[5][0]
        player    = _FakeEntity(999, 999)
        a         = _FakeEntity(head_x, 500.0)
        b         = _FakeEntity(head_x, 500.0)   # mesma posição
        enemy     = _FakeEntity(0, 9999, points=trail_pts)
        entities  = [player, a, b, enemy]
        kills     = check_collisions(entities, player, shield_active=False)
        victims   = [v.id for _, v in kills]
        assert len(victims) == len(set(victims))
