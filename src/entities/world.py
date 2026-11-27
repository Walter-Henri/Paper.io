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

import math
from collections import deque
from typing import List, Set, Tuple

from src.config.game_config import (
    CELL_SIZE, WORLD_COLS, WORLD_ROWS,
    RESPAWN_CLEAR_RADIUS_CELLS,
)


class World:
    def __init__(self) -> None:
        self.cols        = WORLD_COLS
        self.rows        = WORLD_ROWS
        self.cell        = CELL_SIZE
        self.grid:  List[int] = [0] * (self.cols * self.rows)
        self.total_cells = self.cols * self.rows
        self.arena_cells = self.total_cells
        self.playable = bytearray(b"\x01") * self.total_cells
        self.has_mask = False
        self.outline: List[Tuple[float, float]] = []
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
        idx = self._idx(cx, cy)
        if not self.playable[idx]:
            return
        old = self.grid[idx]
        if old != owner_id:
            self.grid[idx] = owner_id
            self._counts[old]      = self._counts.get(old,      0) - 1
            self._counts[owner_id] = self._counts.get(owner_id, 0) + 1

    def is_playable_point(self, x: float, y: float) -> bool:
        cx, cy = self.world_to_cell(x, y)
        if not self.in_bounds_cell(cx, cy):
            return False
        return bool(self.playable[self._idx(cx, cy)])

    def transfer_owner(self, from_id: int, to_id: int) -> int:
        """Passa todas as células de from_id para to_id. Retorna quantas mudaram."""
        if from_id == to_id or from_id == 0 or to_id == 0:
            return 0
        moved = 0
        grid = self.grid
        for i, owner in enumerate(grid):
            if owner == from_id:
                grid[i] = to_id
                moved += 1
        if moved:
            self._counts[from_id] = 0
            self._counts[to_id] = self._counts.get(to_id, 0) + moved
        return moved

    def resolve_motion(self, x: float, y: float,
                       vx: float, vy: float,
                       dt: float, radius: float,
                       slide_sign: int = 0) -> Tuple[float, float, int]:
        """Avança livremente; só desliza se o próximo passo bater na barreira."""
        speed = math.hypot(vx, vy)
        if speed < 1e-4 or dt <= 0:
            return x, y, 0
        return self._motion_step(x, y, vx, vy, dt, radius, slide_sign)[:3]

    def _motion_step(self, x: float, y: float,
                     vx: float, vy: float,
                     dt: float, radius: float,
                     slide_sign: int):
        speed = math.hypot(vx, vy) or 1.0
        ux, uy = vx / speed, vy / speed
        nx = x + vx * dt
        ny = y + vy * dt
        # Desgruda com facilidade: se o passo cabe, sai da barreira na hora.
        if self._body_inside(nx, ny, radius):
            return nx, ny, 0, False, vx, vy

        tx, ty, ix, iy = self._contact_axes(x, y, vx, vy)
        # Preferência: movimento para o interior (desgrudar) se a intenção
        # tiver componente para dentro da área jogável.
        inward = ux * ix + uy * iy
        if inward > 0.25:
            # Tenta um passo puxado para dentro — solta da parede.
            hx, hy = ux * 0.55 + ix * 0.45, uy * 0.55 + iy * 0.45
            n = math.hypot(hx, hy) or 1.0
            hx, hy = hx / n, hy / n
            sx, sy, moved = self._walk(x, y, hx, hy, speed * dt)
            if moved > speed * dt * 0.3:
                return sx, sy, 0, False, hx * speed, hy * speed

        # Lado estável: +1 = à esquerda da velocidade de entrada.
        perp_x, perp_y = -uy, ux
        if tx * perp_x + ty * perp_y < 0:
            tx, ty = -tx, -ty
            ix, iy = -ix, -iy
        dist = speed * dt
        prefer = slide_sign or 1

        def try_dir(hx, hy):
            sx, sy, moved = self._walk(x, y, hx, hy, dist)
            return moved, sx, sy, hx, hy

        candidates = []
        for hx, hy in (
            self._hug_dir(tx, ty, ix, iy, prefer),
            (tx * prefer, ty * prefer),
        ):
            item = try_dir(hx, hy)
            if item[0] > dist * 0.3:
                candidates.append(item)

        if not candidates:
            for hx, hy in (
                self._hug_dir(tx, ty, ix, iy, -prefer),
                (tx * -prefer, ty * -prefer),
            ):
                item = try_dir(hx, hy)
                if item[0] > dist * 0.25:
                    candidates.append(item)
                    prefer = -prefer

        if not candidates:
            # Último recurso: empurra para dentro e libera o stick.
            px, py = self._push_inside(x + ix * 6.0, y + iy * 6.0, ix, iy, radius)
            return px, py, 0, True, ix * speed, iy * speed

        moved, sx, sy, hx, hy = max(candidates, key=lambda it: it[0])
        side = prefer if (hx * tx + hy * ty) * prefer >= 0 else -prefer
        return sx, sy, side, True, hx * speed, hy * speed

    def _hug_dir(self, tx, ty, ix, iy, sign):
        # Viés interno leve: só o bastante para não sair da máscara rasterizada.
        hx = tx * sign + ix * 0.12
        hy = ty * sign + iy * 0.12
        n = math.hypot(hx, hy) or 1.0
        return hx / n, hy / n

    def _walk(self, x, y, hx, hy, dist):
        step = 2.0
        cx, cy = x, y
        moved = 0.0
        while moved + 0.35 < dist:
            remain = dist - moved
            s = step if remain > step else remain
            nx = cx + hx * s
            ny = cy + hy * s
            if not self.is_playable_point(nx, ny):
                lo, hi = 0.0, s
                for _ in range(6):
                    mid = (lo + hi) * 0.5
                    if self.is_playable_point(cx + hx * mid, cy + hy * mid):
                        lo = mid
                    else:
                        hi = mid
                if lo < 0.35:
                    break
                cx += hx * lo
                cy += hy * lo
                moved += lo
                break
            cx, cy = nx, ny
            moved += s
        return cx, cy, moved

    def _body_inside(self, x, y, radius) -> bool:
        return self.is_playable_point(x, y)

    def _push_inside(self, x, y, ix, iy, radius):
        if self._body_inside(x, y, radius):
            return x, y
        for k in range(1, 8):
            px = x + ix * (k * 2.5)
            py = y + iy * (k * 2.5)
            if self._body_inside(px, py, radius):
                return px, py
        return x, y

    def _contact_axes(self, x, y, vx=0.0, vy=0.0):
        if self.has_mask:
            axes = self._mask_axes(x, y, vx, vy)
            if axes is not None:
                return axes
            if len(self.outline) >= 3:
                return self._outline_axes(x, y)
        return self._rect_axes(x, y, 9.0)

    def _mask_axes(self, x, y, vx=0.0, vy=0.0):
        speed = math.hypot(vx, vy)
        if speed > 1.0:
            ux, uy = vx / speed, vy / speed
        else:
            ux, uy = 1.0, 0.0
        ox = oy = 0.0
        hits = 0
        for dist in (4.0, 8.0, 12.0):
            for side in (0.0, -6.0, 6.0):
                px = x + ux * dist + (-uy) * side
                py = y + uy * dist + ux * side
                if self.is_playable_point(px, py):
                    continue
                ox += px - x
                oy += py - y
                hits += 1
        if hits == 0:
            return None
        n = math.hypot(ox, oy) or 1.0
        ox /= n
        oy /= n
        return -oy, ox, -ox, -oy

    def _outline_axes(self, x, y):
        outline = self.outline
        best_d2 = 1e18
        tx = ty = 1.0
        qx = x
        qy = y
        n = len(outline)
        for i in range(n):
            ax, ay = outline[i]
            bx, by = outline[(i + 1) % n]
            ex, ey = bx - ax, by - ay
            len2 = ex * ex + ey * ey
            if len2 < 1e-6:
                continue
            t = ((x - ax) * ex + (y - ay) * ey) / len2
            if t < 0.0:
                t = 0.0
            elif t > 1.0:
                t = 1.0
            px = ax + ex * t
            py = ay + ey * t
            d2 = (x - px) ** 2 + (y - py) ** 2
            if d2 < best_d2:
                best_d2 = d2
                inv = 1.0 / math.sqrt(len2)
                tx, ty = ex * inv, ey * inv
                qx, qy = px, py
        n1x, n1y = -ty, tx
        if self.is_playable_point(qx + n1x * 10.0, qy + n1y * 10.0):
            ix, iy = n1x, n1y
        else:
            ix, iy = ty, -tx
        return tx, ty, ix, iy

    def _rect_axes(self, x, y, radius):
        span_x = self.cols * self.cell
        span_y = self.rows * self.cell
        m = radius
        left, right = x - m, (span_x - m) - x
        top, bottom = y - m, (span_y - m) - y
        nearest = min(left, right, top, bottom)
        if nearest == left:
            return 0.0, 1.0, 1.0, 0.0
        if nearest == right:
            return 0.0, 1.0, -1.0, 0.0
        if nearest == top:
            return 1.0, 0.0, 0.0, 1.0
        return 1.0, 0.0, 0.0, -1.0


    def apply_arena_polygon(self, points: List[Tuple[float, float]]) -> None:
        """Marca como jogáveis só as células dentro do contorno do estado."""
        from src.core.brazil_maps import point_in_polygon
        if len(points) < 3:
            return
        mask = bytearray(self.total_cells)
        count = 0
        for cy in range(self.rows):
            py = (cy + 0.5) * self.cell
            base = cy * self.cols
            for cx in range(self.cols):
                px = (cx + 0.5) * self.cell
                if point_in_polygon(px, py, points):
                    mask[base + cx] = 1
                    count += 1
        if count < 32:
            return
        self.playable = mask
        self.arena_cells = count
        self.has_mask = True
        self.outline = list(points)

    def random_playable_point(self, rng, margin: float = 48.0,
                               attempts: int = 80) -> Tuple[float, float]:
        for _ in range(attempts):
            x = rng.uniform(margin, self.cols * self.cell - margin)
            y = rng.uniform(margin, self.rows * self.cell - margin)
            if self.is_playable_point(x, y):
                return x, y
        return self.playable_spawn()

    def playable_spawn(self) -> Tuple[float, float]:
        """Ponto interior, próximo do centro de massa da área jogável."""
        sx = sy = n = 0
        for cy in range(0, self.rows, 2):
            base = cy * self.cols
            for cx in range(0, self.cols, 2):
                if self.playable[base + cx]:
                    sx += cx
                    sy += cy
                    n += 1
        if not n:
            return self.cols * self.cell * 0.5, self.rows * self.cell * 0.5
        cx = int(sx / n)
        cy = int(sy / n)
        if self.playable[self._idx(cx, cy)]:
            return (cx + 0.5) * self.cell, (cy + 0.5) * self.cell
        for radius in range(1, max(self.cols, self.rows)):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    nx, ny = cx + dx, cy + dy
                    if self.in_bounds_cell(nx, ny) and self.playable[self._idx(nx, ny)]:
                        return (nx + 0.5) * self.cell, (ny + 0.5) * self.cell
        return self.cols * self.cell * 0.5, self.rows * self.cell * 0.5

    def is_own_territory(self, x: float, y: float, owner_id: int) -> bool:
        return self.get_owner(x, y) == owner_id

    def count_owned(self, owner_id: int) -> int:
        return max(0, self._counts.get(owner_id, 0))

    def ownership_percent(self, owner_id: int) -> float:
        base = self.arena_cells or self.total_cells
        return (self.count_owned(owner_id) / base) * 100.0

    def seed_starting_territory(self, x: float, y: float,
                                 owner_id: int,
                                 radius_cells: int = 7,
                                 only_empty: bool = False) -> None:
        """Atribui um disco de células ao dono. only_empty não pisa tinta alheia."""
        cx, cy = self.world_to_cell(x, y)
        r2 = radius_cells * radius_cells
        for dy in range(-radius_cells, radius_cells + 1):
            for dx in range(-radius_cells, radius_cells + 1):
                if dx * dx + dy * dy > r2:
                    continue
                nx, ny = cx + dx, cy + dy
                if not self.in_bounds_cell(nx, ny):
                    continue
                if only_empty and self.grid[self._idx(nx, ny)] not in (0, owner_id):
                    continue
                self.set_owner_cell(nx, ny, owner_id)

    def has_clear_respawn_space(self, cx: int, cy: int,
                                  radius: int = RESPAWN_CLEAR_RADIUS_CELLS) -> bool:
        # Disco de celulas livres e jogaveis ao redor do ponto.
        r2 = radius * radius
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy > r2:
                    continue
                nx, ny = cx + dx, cy + dy
                if not self.in_bounds_cell(nx, ny):
                    return False
                i = self._idx(nx, ny)
                if not self.playable[i] or self.grid[i] != 0:
                    return False
        return True

    def random_unowned_point(self, rng, attempts: int = 120):
        # Ponto livre com espaco minimo para renascer, ou None.
        span_x = self.cols * self.cell
        span_y = self.rows * self.cell
        radius = RESPAWN_CLEAR_RADIUS_CELLS
        for _ in range(attempts):
            x = rng.uniform(0, span_x)
            y = rng.uniform(0, span_y)
            cx, cy = self.world_to_cell(x, y)
            if self.has_clear_respawn_space(cx, cy, radius):
                return (cx + 0.5) * self.cell, (cy + 0.5) * self.cell
        for i, owner in enumerate(self.grid):
            if owner != 0 or not self.playable[i]:
                continue
            cx, cy = i % self.cols, i // self.cols
            if self.has_clear_respawn_space(cx, cy, radius):
                return (cx + 0.5) * self.cell, (cy + 0.5) * self.cell
        return None

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

    def _reachable_local(self, wall: bytearray,
                            min_x: int, min_y: int,
                            max_x: int, max_y: int) -> bytearray:
        """Marca células alcançáveis a partir do exterior da caixa local."""
        cols, rows = self.cols, self.rows
        total = self.total_cells
        seen = bytearray(total)
        queue: deque = deque()

        def push(cx: int, cy: int) -> None:
            if cx < min_x or cy < min_y or cx > max_x or cy > max_y:
                return
            if cx < 0 or cy < 0 or cx >= cols or cy >= rows:
                return
            i = cy * cols + cx
            if wall[i] or seen[i]:
                return
            seen[i] = 1
            queue.append((cx, cy))

        # Sementes: borda da caixa e células não jogáveis (exterior da máscara).
        for cx in range(min_x, max_x + 1):
            push(cx, min_y)
            push(cx, max_y)
        for cy in range(min_y, max_y + 1):
            push(min_x, cy)
            push(max_x, cy)
        for cy in range(min_y, max_y + 1):
            base = cy * cols
            for cx in range(min_x, max_x + 1):
                i = base + cx
                if not self.playable[i] and not wall[i] and not seen[i]:
                    seen[i] = 1
                    queue.append((cx, cy))

        while queue:
            cx, cy = queue.popleft()
            push(cx + 1, cy)
            push(cx - 1, cy)
            push(cx, cy + 1)
            push(cx, cy - 1)
        return seen

    def _thicken_barrier(self, barrier: Set[Tuple[int, int]],
                         radius: int = 1) -> Set[Tuple[int, int]]:
        """Espessa a trilha para a barreira ficar contínua (sem vãos)."""
        if radius <= 0:
            return barrier
        extra: Set[Tuple[int, int]] = set()
        for cx, cy in barrier:
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy > radius * radius + 1:
                        continue
                    nx, ny = cx + dx, cy + dy
                    if self.in_bounds_cell(nx, ny):
                        extra.add((nx, ny))
        barrier |= extra
        return barrier

    def claim_enclosed_area(self,
                             trail_points: List[Tuple[float, float]],
                             owner_id: int) -> int:
        """
        Preenche o interior fechado pela trilha como tinta: qualquer forma
        plana (curva, circular, irregular). Sem buracos internos.
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
        if (sx - ex) ** 2 + (sy - ey) ** 2 <= (self.cell * 3) ** 2:
            barrier |= self._rasterize_segment(ex, ey, sx, sy)

        if not barrier:
            return 0

        self._seal_diagonal_gaps(barrier, owner_id)
        self._bridge_endpoints(barrier, trail_points, owner_id)
        # Trilha um pouco mais grossa: evita vazamento e furações.
        self._thicken_barrier(barrier, radius=1)

        # Território atual do dono entra na vedação (retorno à base).
        own_cells: List[Tuple[int, int]] = []
        cols = self.cols
        for i, owner in enumerate(self.grid):
            if owner == owner_id:
                own_cells.append((i % cols, i // cols))

        min_x = min(c[0] for c in barrier)
        max_x = max(c[0] for c in barrier)
        min_y = min(c[1] for c in barrier)
        max_y = max(c[1] for c in barrier)
        # Inclui território próximo para fechar com a base.
        pad = 6
        for cx, cy in own_cells:
            if (min_x - pad <= cx <= max_x + pad and
                    min_y - pad <= cy <= max_y + pad):
                min_x = min(min_x, cx)
                max_x = max(max_x, cx)
                min_y = min(min_y, cy)
                max_y = max(max_y, cy)
        min_x = max(0, min_x - 2)
        min_y = max(0, min_y - 2)
        max_x = min(self.cols - 1, max_x + 2)
        max_y = min(self.rows - 1, max_y + 2)

        own = bytearray(self.total_cells)
        for cx, cy in own_cells:
            own[self._idx(cx, cy)] = 1

        full = bytearray(own)
        for cx, cy in barrier:
            full[self._idx(cx, cy)] = 1

        reach_base = self._reachable_local(own, min_x, min_y, max_x, max_y)
        reach_full = self._reachable_local(full, min_x, min_y, max_x, max_y)

        claimed = 0
        for cy in range(min_y, max_y + 1):
            base = cy * cols
            for cx in range(min_x, max_x + 1):
                i = base + cx
                if not self.playable[i] or self.grid[i] == owner_id:
                    continue
                is_trail = full[i] and not own[i]
                # Interior: antes era alcançável, agora isolado pela trilha+base.
                newly_inside = (not reach_full[i]) and reach_base[i] and not full[i]
                if is_trail or newly_inside:
                    self.set_owner_cell(cx, cy, owner_id)
                    claimed += 1

        # Segunda passagem: preenche buracos residuals dentro do território.
        claimed += self._fill_owner_holes(owner_id, min_x, min_y, max_x, max_y)
        return claimed

    def _fill_owner_holes(self, owner_id: int,
                          min_x: int, min_y: int,
                          max_x: int, max_y: int) -> int:
        """Preenche células vazias enclausuradas pelo território do dono."""
        cols = self.cols
        # Parede = território do dono (não atravessa).
        wall = bytearray(self.total_cells)
        for cy in range(min_y, max_y + 1):
            base = cy * cols
            for cx in range(min_x, max_x + 1):
                i = base + cx
                if self.grid[i] == owner_id:
                    wall[i] = 1
        reach = self._reachable_local(wall, min_x, min_y, max_x, max_y)
        filled = 0
        for cy in range(min_y, max_y + 1):
            base = cy * cols
            for cx in range(min_x, max_x + 1):
                i = base + cx
                if not self.playable[i] or self.grid[i] != 0:
                    continue
                if not reach[i]:
                    # Vazio isolado do exterior = buraco → preenche.
                    self.set_owner_cell(cx, cy, owner_id)
                    filled += 1
        return filled

    def claim_polygon(self,
                      points: List[Tuple[float, float]],
                      owner_id: int) -> int:
        """Alias para claim_enclosed_area (compatibilidade)."""
        return self.claim_enclosed_area(points, owner_id)
