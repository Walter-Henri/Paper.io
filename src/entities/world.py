"""
world.py — TerritórIO: Edição Brasil
--------------------------------------
Responsabilidade:
    Gerenciar a grade de território do mundo (ownership grid).
    Oferecer operações de leitura, escrita, contagem e captura de área.

Captura:
    A trilha vira uma barreira 4-conectada (Bresenham + célula de canto).
    No retorno à base a vedação é trilha + território já do dono, sem a
    corda reta do fim ao início que cortava ou vazava a área.
    Só entram células que ficaram inacessíveis por causa desta trilha.
    Buracos antigos, já isolados, não são repintados.

Não contém lógica de movimento, colisão, renderização ou IA.
"""

from __future__ import annotations

from collections import deque
from typing import List, Set, Tuple

from src.config.game_config import CELL_SIZE, WORLD_COLS, WORLD_ROWS


class World:
    def __init__(self) -> None:
        self.cols        = WORLD_COLS
        self.rows        = WORLD_ROWS
        self.cell        = CELL_SIZE
        self.grid:  List[int] = [0] * (self.cols * self.rows)
        self.total_cells = self.cols * self.rows
        self._counts: dict = {}

    def _idx(self, cx: int, cy: int) -> int:
        return cy * self.cols + cx

    def in_bounds_cell(self, cx: int, cy: int) -> bool:
        return 0 <= cx < self.cols and 0 <= cy < self.rows

    def world_to_cell(self, x: float, y: float) -> Tuple[int, int]:
        return int(x // self.cell), int(y // self.cell)

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
            self._counts[old]      = self._counts.get(old,      0) - 1
            self._counts[owner_id] = self._counts.get(owner_id, 0) + 1

    def is_own_territory(self, x: float, y: float, owner_id: int) -> bool:
        return self.get_owner(x, y) == owner_id

    def count_owned(self, owner_id: int) -> int:
        return max(0, self._counts.get(owner_id, 0))

    def ownership_percent(self, owner_id: int) -> float:
        return (self.count_owned(owner_id) / self.total_cells) * 100.0

    def seed_starting_territory(self, x: float, y: float,
                                 owner_id: int,
                                 radius_cells: int = 7) -> None:
        """Atribui um disco de células ao dono no início da partida."""
        cx, cy = self.world_to_cell(x, y)
        r2 = radius_cells * radius_cells
        for dy in range(-radius_cells, radius_cells + 1):
            for dx in range(-radius_cells, radius_cells + 1):
                if dx * dx + dy * dy <= r2:
                    self.set_owner_cell(cx + dx, cy + dy, owner_id)

    def clear_owner(self, owner_id: int) -> None:
        """Remove todas as células pertencentes ao dono."""
        for i in range(len(self.grid)):
            if self.grid[i] == owner_id:
                self.grid[i] = 0
        self._counts[owner_id] = 0

    def _rasterize_segment(self,
                           ax: float, ay: float,
                           bx: float, by: float) -> Set[Tuple[int, int]]:
        """Bresenham com célula de canto para a barreira ficar 4-conectada."""
        cells: Set[Tuple[int, int]] = set()
        x0, y0 = int(ax // self.cell), int(ay // self.cell)
        x1, y1 = int(bx // self.cell), int(by // self.cell)

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            if self.in_bounds_cell(x0, y0):
                cells.add((x0, y0))
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            step_x = e2 > -dy
            step_y = e2 < dx
            if step_x and step_y and self.in_bounds_cell(x0 + sx, y0):
                cells.add((x0 + sx, y0))
            if step_x:
                err -= dy
                x0 += sx
            if step_y:
                err += dx
                y0 += sy

        return cells

    def _seal_diagonal_gaps(self,
                            barrier: Set[Tuple[int, int]],
                            owner_id: int) -> None:
        """Fecha cantos entre a trilha e o território já do dono."""
        extra: List[Tuple[int, int]] = []
        for cx, cy in barrier:
            for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                ox, oy = cx + dx, cy + dy
                if not self.in_bounds_cell(ox, oy):
                    continue
                if self.grid[self._idx(ox, oy)] != owner_id:
                    continue
                ex, ey = cx + dx, cy
                if not self.in_bounds_cell(ex, ey) or self.grid[self._idx(ex, ey)] == owner_id:
                    ex, ey = cx, cy + dy
                if self.in_bounds_cell(ex, ey):
                    extra.append((ex, ey))
        barrier.update(extra)

    def _bridge_endpoints(self,
                          barrier: Set[Tuple[int, int]],
                          trail_points: List[Tuple[float, float]],
                          owner_id: int) -> None:
        """Liga as pontas da trilha ao território do dono se a folga for de poucos células.

        Sem isso o flood vaza no vão de 1 célula entre o último ponto fora
        da base e a borda do território, e a área não fecha.
        """
        cell = self.cell
        max_steps = 4
        for px, py in (trail_points[0], trail_points[-1]):
            ecx, ecy = int(px // cell), int(py // cell)
            found: Tuple[int, int] | None = None
            queue: deque = deque([(ecx, ecy, 0)])
            seen = {(ecx, ecy)}
            while queue:
                cx, cy, dist = queue.popleft()
                if not self.in_bounds_cell(cx, cy):
                    continue
                if self.grid[self._idx(cx, cy)] == owner_id:
                    found = (cx, cy)
                    break
                if dist >= max_steps:
                    continue
                for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = (cx + ddx, cy + ddy)
                    if nxt not in seen:
                        seen.add(nxt)
                        queue.append((nxt[0], nxt[1], dist + 1))
            if found is None or found == (ecx, ecy):
                continue
            ax = (ecx + 0.5) * cell
            ay = (ecy + 0.5) * cell
            bx = (found[0] + 0.5) * cell
            by = (found[1] + 0.5) * cell
            barrier |= self._rasterize_segment(ax, ay, bx, by)

    def _reachable(self, wall: bytearray) -> bytearray:
        """1 = célula alcançável a partir da borda do mapa sem cruzar wall."""
        cols, rows = self.cols, self.rows
        total = self.total_cells
        seen = bytearray(total)
        queue: deque = deque()

        def push(cx: int, cy: int) -> None:
            if cx < 0 or cy < 0 or cx >= cols or cy >= rows:
                return
            i = cy * cols + cx
            if wall[i] or seen[i]:
                return
            seen[i] = 1
            queue.append((cx, cy))

        for cx in range(cols):
            push(cx, 0)
            push(cx, rows - 1)
        for cy in range(rows):
            push(0, cy)
            push(cols - 1, cy)

        while queue:
            cx, cy = queue.popleft()
            push(cx + 1, cy)
            push(cx - 1, cy)
            push(cx, cy + 1)
            push(cx, cy - 1)
        return seen

    def claim_enclosed_area(self,
                             trail_points: List[Tuple[float, float]],
                             owner_id: int) -> int:
        """
        Captura o interior realmente fechado pela trilha.

        A reta do último ponto ao primeiro só existe se as pontas já se
        encontram (loop). No retorno à base a vedação é a trilha junto
        com o território atual.
        """
        if len(trail_points) < 3:
            return 0

        barrier: Set[Tuple[int, int]] = set()
        for i in range(len(trail_points) - 1):
            ax, ay = trail_points[i]
            bx, by = trail_points[i + 1]
            barrier |= self._rasterize_segment(ax, ay, bx, by)

        sx, sy = trail_points[0]
        ex, ey = trail_points[-1]
        if (sx - ex) ** 2 + (sy - ey) ** 2 <= (self.cell * 2) ** 2:
            barrier |= self._rasterize_segment(ex, ey, sx, sy)

        if not barrier:
            return 0

        self._seal_diagonal_gaps(barrier, owner_id)
        self._bridge_endpoints(barrier, trail_points, owner_id)

        own = bytearray(self.total_cells)
        for i, owner in enumerate(self.grid):
            if owner == owner_id:
                own[i] = 1

        full = bytearray(own)
        for cx, cy in barrier:
            full[self._idx(cx, cy)] = 1

        reach_base = self._reachable(own)
        reach_full = self._reachable(full)

        claimed = 0
        cols = self.cols
        for i in range(self.total_cells):
            if self.grid[i] == owner_id:
                continue
            is_trail = full[i] and not own[i]
            newly_inside = (not reach_full[i]) and reach_base[i] and not full[i]
            if is_trail or newly_inside:
                self.set_owner_cell(i % cols, i // cols, owner_id)
                claimed += 1
        return claimed

    def claim_polygon(self,
                      points: List[Tuple[float, float]],
                      owner_id: int) -> int:
        """Alias para claim_enclosed_area (compatibilidade)."""
        return self.claim_enclosed_area(points, owner_id)
