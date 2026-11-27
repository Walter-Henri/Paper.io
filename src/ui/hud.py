# Responsabilidade:
# Renderizar todos os elementos da HUD durante a partida:
# barra superior, ranking lateral, indicadores de power-up,
# badge Predador, minimapa exclusivo e notificações em tela.
# Não contém lógica de jogo, colisão ou comportamento de entidades.

from __future__ import annotations
import math
import pygame

from src.config.game_config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, YELLOW,
    WORLD_WIDTH, WORLD_HEIGHT, CELL_SIZE, WORLD_COLS, WORLD_ROWS,
)


class HUD:
    def __init__(self, assets):
        self.assets = assets

    # Entrada principal
    def draw(self, surface: pygame.Surface,
             session,          # GameSession
             paused: bool = False) -> None:
        self._draw_top_bar(surface, session)
        self._draw_ranking(surface, session)
        self._draw_powerup_panel(surface, session)
        self._draw_state_badge(surface, session)
        if session.player.kills >= 4:
            self._draw_predator_badge(surface)
            self._draw_minimap(surface, session)
        if session.player.outside and len(session.player.trail.points) > 15:
            self._draw_danger(surface)
        if session.player.kills >= 4 or session.pu_manager.shield_active:
            self._draw_shield_indicator(surface, session)
        self._draw_notifications(surface, session.notifications)
        if paused:
            self._draw_pause(surface)

    # Barra superior
    def _draw_top_bar(self, surface: pygame.Surface, session) -> None:
        bar = pygame.Surface((SCREEN_WIDTH, 50), pygame.SRCALPHA)
        bar.fill((10, 12, 20, 220))
        surface.blit(bar, (0, 0))

        player = session.player
        font_b = self.assets.font("body")
        font_s = self.assets.font("small")

        score_txt = font_b.render(
            f"{player.skin_name if hasattr(player,'skin_name') else 'Você'}: "
            f"{player.score_percent:.1f}%", True, player.color)
        surface.blit(score_txt, (14, 10))

        alive = sum(1 for e in session.entities if e.alive)
        surface.blit(font_s.render(f"Vivos: {alive}", True, WHITE),
                     (SCREEN_WIDTH//2 - 40, 14))
        surface.blit(font_s.render(f"Eliminações: {player.kills}", True, YELLOW),
                     (SCREEN_WIDTH//2 + 60, 14))

    # Ranking lateral
    def _draw_ranking(self, surface: pygame.Surface, session) -> None:
        ranked = sorted(
            [e for e in session.entities if e.alive],
            key=lambda e: e.score_percent, reverse=True,
        )[:6]

        panel_w = 230
        row_h   = 20
        pad     = 10
        panel_h = pad + (len(ranked)+1) * row_h + pad
        px      = SCREEN_WIDTH - panel_w - 10
        py      = 58

        bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        bg.fill((10, 12, 22, 210))
        surface.blit(bg, (px, py))
        pygame.draw.rect(surface, (55,60,100), (px,py,panel_w,panel_h), 1, border_radius=4)

        font_xs = self.assets.font("tiny")
        hdr     = font_xs.render("RANKING", True, (160,170,220))
        surface.blit(hdr, (px+8, py+4))

        pos_colors = [(255,215,0),(192,192,192),(205,127,50)]
        for i, e in enumerate(ranked):
            ry      = py + pad + (i+1)*row_h
            pc      = pos_colors[i] if i < 3 else (140,140,140)
            is_you  = (e is session.player)

            surface.blit(font_xs.render(f"#{i+1}", True, pc), (px+6, ry))
            pygame.draw.circle(surface, e.color, (px+34, ry+7), 5)

            name = "VOCÊ" if is_you else e.name[:10]
            nc   = (255,255,100) if is_you else (220,220,220)
            surface.blit(font_xs.render(name, True, nc), (px+44, ry))

            pct = font_xs.render(f"{e.score_percent:.1f}%", True, (100,210,255))
            surface.blit(pct, (px + panel_w - pct.get_width() - 8, ry))

    # Painel de power-ups
    def _draw_powerup_panel(self, surface: pygame.Surface,
                             session) -> None:
        pu  = session.pu_manager
        fsm = self.assets.font("small")
        fxs = self.assets.font("tiny")
        pu.draw_hud(surface, fsm, fxs, SCREEN_WIDTH, SCREEN_HEIGHT)

    # Badge estado / nível
    def _draw_state_badge(self, surface: pygame.Surface,
                           session) -> None:
        font = self.assets.font("small")
        txt  = font.render(
            f"Nível {session.level}  •  {session.state_name}", True, (160,185,230))
        bg   = pygame.Surface((txt.get_width()+14, txt.get_height()+7),
                               pygame.SRCALPHA)
        bg.fill((10,12,22,185))
        surface.blit(bg,  (8, 56))
        surface.blit(txt, (15, 60))

    # Badge Predador
    def _draw_predator_badge(self, surface: pygame.Surface) -> None:
        t    = pygame.time.get_ticks() / 380.0
        rc   = int(190 + 65 * (math.sin(t) * 0.5 + 0.5))
        font = self.assets.font("body")

        # Fundo com borda pulsante
        badge_txt = "⚡ PREDADOR ⚡"
        badge     = font.render(badge_txt, True, (rc, 45, 45))
        bx        = SCREEN_WIDTH//2 - badge.get_width()//2
        bw        = badge.get_width() + 24
        bh        = badge.get_height() + 12

        # Glow exterior pulsante
        glow_alpha = int(60 + 40 * math.sin(t * 2))
        for i in range(4, 0, -1):
            gs = pygame.Surface((bw + i*4, bh + i*4), pygame.SRCALPHA)
            pygame.draw.rect(gs, (rc, 20, 20, glow_alpha),
                             gs.get_rect(), i*2, border_radius=8)
            surface.blit(gs, (bx - 12 - i*2, 6 - i*2))

        bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
        bg.fill((22, 0, 0, 200))
        pygame.draw.rect(bg, (rc, 30, 30, 180), bg.get_rect(), 2, border_radius=6)
        surface.blit(bg,    (bx - 12, 6))
        surface.blit(badge, (bx, 12))

    # Minimapa Predador (aprimorado)
    def _draw_minimap(self, surface: pygame.Surface, session) -> None:
        mm   = 150
        mm_x = SCREEN_WIDTH  - mm - 12
        mm_y = SCREEN_HEIGHT - mm - 100
        sc   = mm / max(WORLD_WIDTH, WORLD_HEIGHT)
        t    = pygame.time.get_ticks() / 1000.0

        # Painel de fundo com borda animada
        bg = pygame.Surface((mm, mm), pygame.SRCALPHA)
        bg.fill((8, 10, 20, 230))
        surface.blit(bg, (mm_x, mm_y))

        border_alpha = int(160 + 60 * math.sin(t * 2))
        pygame.draw.rect(surface, (200, 50, 50, border_alpha),
                         (mm_x, mm_y, mm, mm), 2, border_radius=4)

        # Território dentro do contorno do estado
        step = 3
        cm   = session._color_map
        grid = session.world.grid
        playable = session.world.playable
        has_mask = session.world.has_mask
        for cy in range(0, WORLD_ROWS, step):
            for cx in range(0, WORLD_COLS, step):
                idx = cy * WORLD_COLS + cx
                if has_mask and not playable[idx]:
                    continue
                owner = grid[idx]
                if not owner:
                    if has_mask:
                        mx = int(cx * CELL_SIZE * sc) + mm_x
                        my = int(cy * CELL_SIZE * sc) + mm_y
                        ssz = max(2, int(CELL_SIZE * step * sc) + 1)
                        pygame.draw.rect(surface, (28, 36, 52), (mx, my, ssz, ssz))
                    continue
                color = cm.get(owner)
                if not color:
                    continue
                mx  = int(cx * CELL_SIZE * sc) + mm_x
                my  = int(cy * CELL_SIZE * sc) + mm_y
                ssz = max(2, int(CELL_SIZE * step * sc) + 1)
                pygame.draw.rect(surface, color, (mx, my, ssz, ssz))

        outline = session.world.outline
        if len(outline) >= 3:
            pts = [(int(x * sc) + mm_x, int(y * sc) + mm_y) for x, y in outline]
            pygame.draw.lines(surface, (150, 198, 255), True, pts, 2)

        # Radar sweep (linha giratória sutil)
        sweep_angle = (t * 60) % 360
        sweep_rad   = math.radians(sweep_angle)
        center_mx   = mm_x + mm // 2
        center_my   = mm_y + mm // 2
        sweep_x     = center_mx + int(math.cos(sweep_rad) * mm // 2)
        sweep_y     = center_my + int(math.sin(sweep_rad) * mm // 2)
        pygame.draw.line(surface, (200, 50, 50, 60),
                         (center_mx, center_my), (sweep_x, sweep_y), 1)

        # Power-ups no minimapa
        for item in session.pu_manager.items:
            mx = int(item.x * sc) + mm_x
            my = int(item.y * sc) + mm_y
            if mm_x <= mx <= mm_x+mm and mm_y <= my <= mm_y+mm:
                r_pu = 3
                s_pu = pygame.Surface((r_pu*2+2, r_pu*2+2), pygame.SRCALPHA)
                pygame.draw.circle(s_pu, (*item.color, 220), (r_pu+1, r_pu+1), r_pu)
                surface.blit(s_pu, (mx-r_pu-1, my-r_pu-1))

        # Entidades com indicadores diferenciados
        for e in session.entities:
            if not e.alive:
                continue
            mx = int(e.x * sc) + mm_x
            my = int(e.y * sc) + mm_y
            if not (mm_x <= mx <= mm_x+mm and mm_y <= my <= mm_y+mm):
                continue

            if e is session.player:
                # Jogador: círculo branco + anéis de pulso
                r_p  = 5
                for ring in range(2):
                    rs = pygame.Surface(((r_p+ring+2)*2+2, (r_p+ring+2)*2+2), pygame.SRCALPHA)
                    pygame.draw.circle(rs, (255, 255, 255, 80 - ring*30),
                                       (r_p+ring+2+1, r_p+ring+2+1), r_p+ring+1, 1)
                    surface.blit(rs, (mx-r_p-ring-2, my-r_p-ring-2))
                pygame.draw.circle(surface, (255,255,255), (mx, my), r_p)
                pygame.draw.circle(surface, (200,200,255), (mx, my), r_p, 1)
            else:
                # Bots: círculo colorido com estado indicado por borda
                state_col = {
                    "hunt":      (255, 60, 60),
                    "intercept": (255, 140, 0),
                    "evade":     (255, 220, 0),
                    "collect_pu":(100, 255, 200),
                }.get(getattr(e, "state", "expand"), (160, 160, 160))
                pygame.draw.circle(surface, (0,0,0),   (mx, my), 4)
                pygame.draw.circle(surface, e.color,   (mx, my), 3)
                pygame.draw.circle(surface, state_col, (mx, my), 3, 1)

        # Painel de stats Predador (lado esquerdo do minimapa)
        self._draw_predator_stats(surface, session, mm_x, mm_y, mm)

        # Label
        lbl = self.assets.font("tiny").render("⚡ RADAR", True, (220, 80, 80))
        surface.blit(lbl, (mm_x + 4, mm_y - 16))

    def _draw_predator_stats(self, surface: pygame.Surface,
                              session, mm_x: int, mm_y: int, mm: int) -> None:
        """Painel lateral com estatísticas do modo Predador."""
        panel_w = 110
        px      = mm_x - panel_w - 6
        py      = mm_y

        bg = pygame.Surface((panel_w, mm), pygame.SRCALPHA)
        bg.fill((10, 0, 0, 215))
        pygame.draw.rect(bg, (180, 30, 30, 160), bg.get_rect(), 1, border_radius=4)
        surface.blit(bg, (px, py))

        font_xs = self.assets.font("tiny")
        y_off   = py + 6

        # Título
        title = font_xs.render("PREDADOR", True, (220, 60, 60))
        surface.blit(title, (px + panel_w//2 - title.get_width()//2, y_off))
        y_off += 18

        # Kills
        kills_surf = font_xs.render(f"Kills: {session.player.kills}", True, (255, 180, 100))
        surface.blit(kills_surf, (px + 6, y_off))
        y_off += 16

        # Território do jogador
        pct = session.player.score_percent
        pct_surf = font_xs.render(f"Área: {pct:.1f}%", True, (100, 220, 255))
        surface.blit(pct_surf, (px + 6, y_off))
        y_off += 16

        # Bots vivos e seus estados
        alive_bots = [(e, getattr(e, "state", "?")) for e in session.entities
                      if e is not session.player and e.alive]
        for e, state in alive_bots[:6]:
            # Cor por estado
            sc = {"hunt": (255,80,80), "evade":(255,220,0),
                  "intercept":(255,140,0)}.get(state, (160,160,160))
            pygame.draw.circle(surface, e.color,  (px+9,  y_off+5), 4)
            pygame.draw.circle(surface, sc,       (px+9,  y_off+5), 4, 1)
            name_s = font_xs.render(e.name[:8], True, (200, 200, 200))
            surface.blit(name_s, (px + 16, y_off))
            pct_b  = font_xs.render(f"{e.score_percent:.0f}%", True, sc)
            surface.blit(pct_b, (px + panel_w - pct_b.get_width() - 4, y_off))
            y_off += 15
            if y_off > py + mm - 10:
                break

    # Alertas e indicadores
    def _draw_danger(self, surface: pygame.Surface) -> None:
        t     = pygame.time.get_ticks() / 300.0
        alpha = int(180 + 75 * (math.sin(t) * 0.5 + 0.5))
        warn  = self.assets.font("small").render(
            "⚠ VULNERÁVEL — feche a trilha!", True, (255,100,60))
        warn.set_alpha(alpha)
        surface.blit(warn, warn.get_rect(center=(SCREEN_WIDTH//2, 70)))

    def _draw_shield_indicator(self, surface: pygame.Surface,
                                session) -> None:
        if not session.pu_manager.shield_active:
            return
        # Anel pulsante na borda da tela
        t = pygame.time.get_ticks() / 300.0
        alpha = int(60 + 40 * math.sin(t))
        border = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(border, (100,255,100,alpha),
                         border.get_rect(), 6, border_radius=4)
        surface.blit(border, (0, 0))

    # Notificações
    def _draw_notifications(self, surface: pygame.Surface,
                             notifications: list) -> None:
        font = self.assets.font("body")
        for i, n in enumerate(notifications[-3:]):
            frac  = min(1.0, n["life"] / 2.5)
            alpha = int(frac * 255)
            surf  = font.render(n["text"], True, n["color"])
            bg    = pygame.Surface((surf.get_width()+22, surf.get_height()+10),
                                   pygame.SRCALPHA)
            bg.fill((18,20,30, min(190,alpha)))
            x = SCREEN_WIDTH//2  - surf.get_width()//2
            y = SCREEN_HEIGHT//2 - 90 - i*44
            surface.blit(bg,   (x-11, y-5))
            surf.set_alpha(alpha)
            surface.blit(surf, (x, y))

    # Pausa
    def _draw_pause(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,160))
        surface.blit(overlay, (0,0))
        font = self.assets.font("title_sm")
        brand = self.assets.font("small").render("PAPERWORLDS", True, (180, 210, 255))
        surface.blit(brand, brand.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 48)))
        txt  = font.render("PAUSADO  —  P para continuar", True, (255,220,50))
        surface.blit(txt, txt.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))
