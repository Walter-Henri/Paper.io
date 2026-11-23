# Responsabilidade:
# Gerenciar a grade de território do mundo (ownership grid).
# Oferecer operações de leitura, escrita, contagem e captura por polígono.
# Não contém lógica de movimento, colisão, renderização ou IA.

from __future__ import annotations
from typing import List, Tuple, Set

from src.config.game_config import CELL_SIZE, WORLD_COLS, WORLD_ROWS


class World:
    def __init__(self):
        self.cols        = WORLD_COLS
        self.rows        = WORLD_ROWS
        self.cell        = CELL_SIZE
        self.grid:       List[int] = [0] * (self.cols * self.rows)
        self.total_cells = self.cols * self.rows
        self._counts:    dict      = {}

    # ── Helpers de índice e coordenada ────────────────────────────────────────

    def _idx(self, cx: int, cy: int) -> int:
        return cy * self.cols + cx

    def in_bounds_cell(self, cx: int, cy: int) -> bool:
        return 0 <= cx < self.cols and 0 <= cy < self.rows

    def world_to_cell(self, x: float, y: float) -> Tuple[int, int]:
        return int(x // self.cell), int(y // self.cell)

    # ── Acesso à grid ──────────────────────────────────────────────────────────

    def get_owner(self, x: float, y: float) -> int:
        cx, cy = self.world_to_cell(x, y)
        if not self.in_bounds_cell(cx, cy):
            return -1
        return self.grid[self._idx(cx, cy)]

    def set_owner_cell(self, cx: int, cy: int, owner_id: int) -> None:
        if not self.in_bounds_cell(cx, cy):
            return
        old = self.grid[self._idx(cx, cy)]
        if old != owner_id:
            self.grid[self._idx(cx, cy)] = owner_id
            self._counts[old]       = self._counts.get(old, 0)       - 1
            self._counts[owner_id]  = self._counts.get(owner_id, 0)  + 1

    def is_own_territory(self, x: float, y: float, owner_id: int) -> bool:
        return self.get_owner(x, y) == owner_id

    # ── Contagem e pontuação ───────────────────────────────────────────────────

    def count_owned(self, owner_id: int) -> int:
        return max(0, self._counts.get(owner_id, 0))

    def ownership_percent(self, owner_id: int) -> float:
        return (self.count_owned(owner_id) / self.total_cells) * 100.0

    # ── Operações em área ──────────────────────────────────────────────────────

    def seed_starting_territory(self, x: float, y: float,
                                 owner_id: int,
                                 radius_cells: int = 7) -> None:
        cx, cy = self.world_to_cell(x, y)
        r2 = radius_cells * radius_cells
        for dy in range(-radius_cells, radius_cells + 1):
            for dx in range(-radius_cells, radius_cells + 1):
                if dx * dx + dy * dy <= r2:
                    self.set_owner_cell(cx + dx, cy + dy, owner_id)

    def clear_owner(self, owner_id: int) -> None:
        for i in range(len(self.grid)):
            if self.grid[i] == owner_id:
                self.grid[i] = 0
        self._counts[owner_id] = 0

    def claim_polygon(self, points: List[Tuple[float, float]],
                      owner_id: int) -> int:
        """Reivindica células dentro do polígono via ray-casting."""
        if len(points) < 3:
            return 0
        xs      = [p[0] for p in points]
        ys      = [p[1] for p in points]
        min_cx  = max(0,            int(min(xs) // self.cell) - 1)
        max_cx  = min(self.cols-1,  int(max(xs) // self.cell) + 1)
        min_cy  = max(0,            int(min(ys) // self.cell) - 1)
        max_cy  = min(self.rows-1,  int(max(ys) // self.cell) + 1)
        claimed = 0
        for cy in range(min_cy, max_cy + 1):
            for cx in range(min_cx, max_cx + 1):
                wx = (cx + 0.5) * self.cell
                wy = (cy + 0.5) * self.cell
                if self._point_in_polygon(wx, wy, points):
                    old = self.grid[self._idx(cx, cy)]
                    if old != owner_id:
                        self.set_owner_cell(cx, cy, owner_id)
                        claimed += 1
        return claimed

    @staticmethod
    def _point_in_polygon(x: float, y: float,
                           poly: List[Tuple[float, float]]) -> bool:
        n      = len(poly)
        inside = False
        j      = n - 1
        for i in range(n):
            xi, yi = poly[i]
            xj, yj = poly[j]
            if ((yi > y) != (yj > y)) and \
               (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi):
                inside = not inside
            j = i
        return inside

    def get_leader_id(self, alive_ids: Set[int]) -> int:
        best_id, best = 0, -1
        for oid in alive_ids:
            c = self.count_owned(oid)
            if c > best:
                best    = c
                best_id = oid
        return best_id
