"""
test_trail.py — TerritórIO: Edição Brasil
-------------------------------------------
Testes para src/entities/trail.py.

Cobre:
    - Adição de pontos (com distância mínima respeitada)
    - Limpeza da trilha
    - Cálculo de comprimento
    - Detecção de aproximação ao ponto inicial

Execute com:
    python -m pytest tests/test_trail.py -v
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import math
import pytest
from src.entities.trail import Trail


@pytest.fixture
def trail() -> Trail:
    return Trail(owner_id=1, color=(100, 200, 100))


class TestAddPoint:
    def test_first_point_always_added(self, trail: Trail):
        trail.add_point(10.0, 20.0, min_dist=5.0)
        assert len(trail.points) == 1

    def test_too_close_point_ignored(self, trail: Trail):
        trail.add_point(0.0, 0.0)
        trail.add_point(1.0, 0.0, min_dist=5.0)   # distância 1 < 5
        assert len(trail.points) == 1

    def test_far_enough_point_added(self, trail: Trail):
        trail.add_point(0.0, 0.0)
        trail.add_point(10.0, 0.0, min_dist=5.0)
        assert len(trail.points) == 2

    def test_multiple_points(self, trail: Trail):
        for i in range(5):
            trail.add_point(float(i * 10), 0.0, min_dist=5.0)
        assert len(trail.points) == 5


class TestClear:
    def test_clear_empties_points(self, trail: Trail):
        trail.add_point(0.0, 0.0)
        trail.add_point(10.0, 0.0)
        trail.clear()
        assert len(trail.points) == 0

    def test_clear_resets_active(self, trail: Trail):
        trail.active = False
        trail.clear()
        assert trail.active is True


class TestLength:
    def test_empty_trail_length_zero(self, trail: Trail):
        assert trail.length() == pytest.approx(0.0)

    def test_single_point_length_zero(self, trail: Trail):
        trail.add_point(0.0, 0.0)
        assert trail.length() == pytest.approx(0.0)

    def test_two_points_length(self, trail: Trail):
        trail.add_point(0.0, 0.0, min_dist=0)
        trail.add_point(3.0, 4.0, min_dist=0)
        assert trail.length() == pytest.approx(5.0, abs=1e-5)

    def test_multiple_segments(self, trail: Trail):
        # Triângulo 3-4-5: dois lados de 5
        trail.add_point(0.0, 0.0, min_dist=0)
        trail.add_point(3.0, 4.0, min_dist=0)
        trail.add_point(6.0, 0.0, min_dist=0)
        assert trail.length() == pytest.approx(5.0 + 5.0, abs=1e-5)


class TestIsNearStart:
    def test_too_few_points_returns_false(self, trail: Trail):
        trail.add_point(0.0, 0.0, min_dist=0)
        trail.add_point(5.0, 0.0, min_dist=0)
        assert trail.is_near_start(5.0, 0.0) is False

    def test_near_start_detected(self, trail: Trail):
        # Adiciona 6 pontos e checa o início
        for i in range(6):
            trail.add_point(float(i * 10), 0.0, min_dist=0)
        # Posição próxima ao ponto inicial (0,0)
        assert trail.is_near_start(5.0, 0.0, threshold=10.0) is True

    def test_far_from_start_not_detected(self, trail: Trail):
        for i in range(6):
            trail.add_point(float(i * 10), 0.0, min_dist=0)
        # Posição longe do início
        assert trail.is_near_start(500.0, 500.0, threshold=10.0) is False
