"""
test_world.py — TerritórIO: Edição Brasil
-------------------------------------------
Testes automatizados para src/entities/world.py.

Cobre:
    - Inicialização da grade
    - Leitura e escrita de ownership
    - Verificação de território próprio
    - Contagem e porcentagem de território
    - Seed de território inicial
    - Limpeza de dono
    - Captura de polígono (claim_polygon)
    - Consulta de líder

Execute com:
    python -m pytest tests/test_world.py -v
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from src.entities.world import World
from src.config.game_config import CELL_SIZE, WORLD_COLS, WORLD_ROWS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def world() -> World:
    """Instância limpa de World para cada teste."""
    return World()


# ---------------------------------------------------------------------------
# Inicialização
# ---------------------------------------------------------------------------

class TestWorldInit:
    def test_grid_size(self, world: World) -> None:
        """Grade deve ter WORLD_COLS * WORLD_ROWS células."""
        assert len(world.grid) == WORLD_COLS * WORLD_ROWS

    def test_grid_starts_empty(self, world: World) -> None:
        """Todas as células devem iniciar com owner = 0."""
        assert all(v == 0 for v in world.grid)

    def test_total_cells(self, world: World) -> None:
        """total_cells deve corresponder ao produto de cols x rows."""
        assert world.total_cells == WORLD_COLS * WORLD_ROWS


# ---------------------------------------------------------------------------
# Leitura e escrita de células
# ---------------------------------------------------------------------------

class TestOwnership:
    def test_set_and_get_owner(self, world: World) -> None:
        """set_owner_cell deve persistir e get_owner deve retornar o valor."""
        world.set_owner_cell(5, 5, owner_id=1)
        wx = 5 * CELL_SIZE + CELL_SIZE // 2
        wy = 5 * CELL_SIZE + CELL_SIZE // 2
        assert world.get_owner(wx, wy) == 1

    def test_out_of_bounds_returns_minus_one(self, world: World) -> None:
        """Coordenadas fora da grade devem retornar -1."""
        assert world.get_owner(-10, -10) == -1
        assert world.get_owner(99_999, 99_999) == -1

    def test_is_own_territory(self, world: World) -> None:
        """is_own_territory deve retornar True somente para o dono correto."""
        world.set_owner_cell(10, 10, owner_id=2)
        wx = 10 * CELL_SIZE + 1
        wy = 10 * CELL_SIZE + 1
        assert world.is_own_territory(wx, wy, owner_id=2) is True
        assert world.is_own_territory(wx, wy, owner_id=3) is False

    def test_overwrite_owner(self, world: World) -> None:
        """Reescrever uma célula deve atualizar corretamente o dono."""
        world.set_owner_cell(2, 2, owner_id=1)
        world.set_owner_cell(2, 2, owner_id=7)
        wx = 2 * CELL_SIZE + 1
        wy = 2 * CELL_SIZE + 1
        assert world.get_owner(wx, wy) == 7


# ---------------------------------------------------------------------------
# Contagem e porcentagem
# ---------------------------------------------------------------------------

class TestCounting:
    def test_count_owned_increases(self, world: World) -> None:
        """count_owned deve aumentar ao atribuir células."""
        for cx in range(5):
            for cy in range(5):
                world.set_owner_cell(cx, cy, owner_id=1)
        assert world.count_owned(1) == 25

    def test_count_owned_zero_initially(self, world: World) -> None:
        """count_owned deve ser 0 antes de qualquer atribuição."""
        assert world.count_owned(99) == 0

    def test_ownership_percent_range(self, world: World) -> None:
        """ownership_percent deve estar entre 0 e 100."""
        world.set_owner_cell(0, 0, owner_id=1)
        pct = world.ownership_percent(1)
        assert 0.0 <= pct <= 100.0

    def test_ownership_percent_full(self, world: World) -> None:
        """Dono de todas as células deve ter ~100%."""
        for cy in range(WORLD_ROWS):
            for cx in range(WORLD_COLS):
                world.set_owner_cell(cx, cy, owner_id=5)
        pct = world.ownership_percent(5)
        assert abs(pct - 100.0) < 0.01


# ---------------------------------------------------------------------------
# Seed e limpeza
# ---------------------------------------------------------------------------

class TestSeedAndClear:
    def test_seed_creates_territory(self, world: World) -> None:
        """seed_starting_territory deve atribuir células ao redor do ponto."""
        cx = WORLD_COLS // 2
        cy = WORLD_ROWS // 2
        world.seed_starting_territory(
            cx * CELL_SIZE, cy * CELL_SIZE, owner_id=3, radius_cells=5
        )
        assert world.count_owned(3) > 0

    def test_seed_radius_respected(self, world: World) -> None:
        """Células fora do raio não devem ser atribuídas."""
        world.seed_starting_territory(0, 0, owner_id=4, radius_cells=2)
        # Célula bem distante não deve ser do dono 4
        wx = 20 * CELL_SIZE
        wy = 20 * CELL_SIZE
        assert world.get_owner(wx, wy) != 4

    def test_clear_owner(self, world: World) -> None:
        """clear_owner deve remover todas as células do dono informado."""
        world.set_owner_cell(1, 1, owner_id=6)
        world.set_owner_cell(2, 2, owner_id=6)
        world.clear_owner(6)
        assert world.count_owned(6) == 0


# ---------------------------------------------------------------------------
# Captura de polígono
# ---------------------------------------------------------------------------

class TestClaimPolygon:
    def test_claim_simple_square(self, world: World) -> None:
        """Um quadrado fechado deve capturar células internas."""
        s = CELL_SIZE * 10   # lado do quadrado em pixels
        cx = 100
        cy = 100
        square = [
            (cx,     cy),
            (cx + s, cy),
            (cx + s, cy + s),
            (cx,     cy + s),
            (cx,     cy),
        ]
        claimed = world.claim_polygon(square, owner_id=8)
        assert claimed > 0

    def test_claim_does_not_affect_outside(self, world: World) -> None:
        """Células fora do polígono não devem ser capturadas."""
        # Polígono pequeno no canto
        s = CELL_SIZE * 3
        poly = [(0, 0), (s, 0), (s, s), (0, s), (0, 0)]
        world.claim_polygon(poly, owner_id=9)
        # Ponto bem afastado
        far_x = WORLD_COLS * CELL_SIZE - CELL_SIZE
        far_y = WORLD_ROWS * CELL_SIZE - CELL_SIZE
        assert world.get_owner(far_x, far_y) != 9

    def test_claim_empty_polygon_returns_zero(self, world: World) -> None:
        """Polígono vazio ou com menos de 3 pontos deve retornar 0."""
        assert world.claim_polygon([], owner_id=1) == 0
        assert world.claim_polygon([(0, 0), (10, 10)], owner_id=1) == 0


# ---------------------------------------------------------------------------
# Líder
# ---------------------------------------------------------------------------

class TestLeader:
    def test_get_leader_id(self, world: World) -> None:
        """get_leader_id deve retornar o dono com mais células."""
        world.set_owner_cell(0, 0, owner_id=1)
        for cx in range(10):
            for cy in range(10):
                world.set_owner_cell(cx, cy, owner_id=2)
        leader = world.get_leader_id({1, 2})
        assert leader == 2
