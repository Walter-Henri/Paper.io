# Responsabilidade:
# Implementar as cinco telas de interface: menu principal, seleção de skin,
# pausa, game over e vitória. Gerenciar eventos, animações de UI e transições.
# Não contém lógica de jogo, colisão, power-ups ou comportamento de entidades.

from __future__ import annotations
import random
import math
import pygame
from typing import Optional

from src.config.game_config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, YELLOW, GREEN, SKINS,
)


# ── Botão reutilizável ────────────────────────────────────────────────────────

class Button:
    def __init__(self, rect: pygame.Rect, text: str,
                 color=(60, 120, 220), font=None):
        self.rect    = rect
        self.text    = text
        self.color   = color
        self.font    = font
        self.hovered = False

    def update(self, mouse_pos) -> None:
        self.hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, surface: pygame.Surface) -> None:
        c  = tuple(min(255, v+40) for v in self.color) if self.hovered else self.color
        bd = tuple(min(255, v+80) for v in c)
        sh = self.rect.inflate(6, 6)
        shadow = pygame.Surface((sh.width, sh.height), pygame.SRCALPHA)
        shadow.fill((0,0,0,0))
        pygame.draw.rect(shadow, (0,0,0,80), shadow.get_rect(), border_radius=14)
        surface.blit(shadow, sh.topleft)
        pygame.draw.rect(surface, c,  self.rect, border_radius=12)
        pygame.draw.rect(surface, bd, self.rect, 2 if not self.hovered else 3,
                         border_radius=12)
        if self.font:
            lbl = self.font.render(self.text, True, WHITE)
            surface.blit(lbl, lbl.get_rect(center=self.rect.center))

    def clicked(self, event: pygame.event.Event) -> bool:
        return (event.type == pygame.MOUSEBUTTONDOWN and
                event.button == 1 and
                self.rect.collidepoint(event.pos))


# ── Menu Principal ────────────────────────────────────────────────────────────

class MainMenu:
    def __init__(self, assets):
        self.assets     = assets
        self.show_help  = False
        self._pulse     = 0.0
        self._particles = [
            {
                "x":    random.uniform(0, SCREEN_WIDTH),
                "y":    random.uniform(0, SCREEN_HEIGHT),
                "vx":   random.uniform(-18, 18),
                "vy":   random.uniform(-18, 18),
                "r":    random.randint(3, 8),
                "color":SKINS[i % len(SKINS)]["primary"],
                "alpha":random.randint(35, 100),
            }
            for i in range(55)
        ]
        self._selected  = 0
        self._options   = ["Jogar", "Como Jogar", "Sair"]
        self._btn_rects = []

    def update(self, dt: float) -> None:
        self._pulse += dt * 2.2
        for p in self._particles:
            p["x"] = (p["x"] + p["vx"] * dt) % SCREEN_WIDTH
            p["y"] = (p["y"] + p["vy"] * dt) % SCREEN_HEIGHT

    def handle_event(self, event: pygame.event.Event) -> str:
        if self.show_help:
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.show_help = False
            return ""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self._selected = (self._selected - 1) % len(self._options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._selected = (self._selected + 1) % len(self._options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self._activate(self._selected)
        if event.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self._btn_rects):
                if r.collidepoint(event.pos):
                    self._selected = i
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self._btn_rects):
                if r.collidepoint(event.pos):
                    return self._activate(i)
        return ""

    def _activate(self, index: int) -> str:
        opt = self._options[index]
        if opt == "Jogar":        return "play"
        if opt == "Sair":         return "quit"
        if opt == "Como Jogar":   self.show_help = True
        return ""

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((18, 20, 30))
        for i in range(10):
            sh = 18 + i*2
            pygame.draw.rect(surface, (sh, sh+3, sh+9),
                             (0, i*(SCREEN_HEIGHT//10), SCREEN_WIDTH, SCREEN_HEIGHT//10+2))
        for x in range(0, SCREEN_WIDTH, 44):
            pygame.draw.line(surface, (28,32,46),(x,0),(x,SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, 44):
            pygame.draw.line(surface, (28,32,46),(0,y),(SCREEN_WIDTH,y))
        for p in self._particles:
            ps = pygame.Surface((p["r"]*2, p["r"]*2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p["color"],p["alpha"]), (p["r"],p["r"]), p["r"])
            surface.blit(ps, (int(p["x"]), int(p["y"])))
        if self.show_help:
            self._draw_help(surface)
            self._btn_rects = []
            return
        t  = math.sin(self._pulse)*0.5+0.5
        tc = (int(60+180*t), int(130+80*(1-t)), int(220+35*t))
        font_title = self.assets.font("title")
        title  = font_title.render("TerritórIO", True, tc)
        shadow = font_title.render("TerritórIO", True, (20,15,5))
        tr = title.get_rect(center=(SCREEN_WIDTH//2, 148))
        surface.blit(shadow, (tr.x+3, tr.y+3))
        surface.blit(title,  tr)
        sub = self.assets.font("small").render(
            "Edição Brasil  ·  Python  ·  Pygame  ·  27 estados",
            True, (145,158,185))
        surface.blit(sub, sub.get_rect(center=(SCREEN_WIDTH//2, 215)))
        self._btn_rects = []
        btn_colors = {
            "Jogar":      ((30,150,70),  (50,200,100)),
            "Como Jogar": ((50,90,160),  (80,130,210)),
            "Sair":       ((150,40,40),  (200,60,60)),
        }
        mouse = pygame.mouse.get_pos()
        for i, opt in enumerate(self._options):
            cy  = 318 + i*80
            box = pygame.Rect(0,0,290,58)
            box.center = (SCREEN_WIDTH//2, cy)
            self._btn_rects.append(box)
            hov = box.collidepoint(mouse) or i == self._selected
            norm, hi = btn_colors[opt]
            bg_col = hi if hov else norm
            bd_col = tuple(min(255,c+70) for c in bg_col)
            sh = box.inflate(6,6)
            ss = pygame.Surface((sh.width,sh.height),pygame.SRCALPHA)
            pygame.draw.rect(ss,(0,0,0,80),ss.get_rect(),border_radius=14)
            surface.blit(ss,sh.topleft)
            pygame.draw.rect(surface, bg_col, box, border_radius=12)
            pygame.draw.rect(surface, bd_col, box, 3 if hov else 2, border_radius=12)
            lbl = self.assets.font("body").render(opt,True,YELLOW if hov else WHITE)
            surface.blit(lbl, lbl.get_rect(center=box.center))
        hint = self.assets.font("tiny").render(
            "Setas / WASD  ·  Enter para confirmar  ·  M mute", True, (100,110,130))
        surface.blit(hint, hint.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT-36)))

    def _draw_help(self, surface: pygame.Surface) -> None:
        pw, ph = 640, 460
        px = SCREEN_WIDTH//2  - pw//2
        py = SCREEN_HEIGHT//2 - ph//2
        panel = pygame.Surface((pw,ph),pygame.SRCALPHA)
        panel.fill((14,16,26,230))
        surface.blit(panel,(px,py))
        pygame.draw.rect(surface,(60,80,150),(px,py,pw,ph),2,border_radius=10)
        lines = [
            ("COMO JOGAR",True,YELLOW),("",False,WHITE),
            ("Mova com Setas ou WASD",False,WHITE),
            ("Saia do território para traçar uma trilha",False,WHITE),
            ("Feche o loop para conquistar a área",False,WHITE),
            ("Corte a trilha inimiga para eliminá-los",False,WHITE),
            ("NÃO deixe ninguém cortar SUA trilha",False,(255,120,80)),
            ("",False,WHITE),
            ("Power-ups coletáveis:",True,(200,200,255)),
            ("✦ EXPANSÃO — dobra tamanho por 4s",False,(255,165,0)),
            ("▶ TURBO — dobra velocidade por 3s",False,(0,220,255)),
            ("● BOMBA — explosão de tinta ao redor",False,(255,80,80)),
            ("◈ ESCUDO — imunidade por 3s",False,(100,255,100)),
            ("◉ VISÃO — zoom out por 5s",False,(200,150,255)),
            ("",False,WHITE),
            ("4+ eliminações → PREDADOR + minimapa",False,(255,200,80)),
            ("",False,WHITE),
            ("Clique ou ESC para voltar",False,(140,140,160)),
        ]
        y = py+22
        for text,big,color in lines:
            if not text:
                y+=16; continue
            font = self.assets.font("body") if big else self.assets.font("small")
            surf = font.render(text,True,color)
            surface.blit(surf, surf.get_rect(center=(SCREEN_WIDTH//2,y)))
            y += 34 if big else 26


# ── Seleção de Skin ───────────────────────────────────────────────────────────

class SkinSelect:
    def __init__(self, assets):
        self.assets      = assets
        self.selected    = 0
        self._card_rects = []
        self._pulse      = 0.0

    def handle_event(self, event: pygame.event.Event) -> str:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT,  pygame.K_a): self.selected=(self.selected-1)%len(SKINS)
            if event.key in (pygame.K_RIGHT, pygame.K_d): self.selected=(self.selected+1)%len(SKINS)
            if event.key in (pygame.K_UP,    pygame.K_w): self.selected=(self.selected-5)%len(SKINS)
            if event.key in (pygame.K_DOWN,  pygame.K_s): self.selected=(self.selected+5)%len(SKINS)
            if event.key in (pygame.K_RETURN,pygame.K_SPACE): return "confirm"
            if event.key == pygame.K_ESCAPE: return "back"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
            for i,r in enumerate(self._card_rects):
                if r.collidepoint(event.pos):
                    if self.selected==i: return "confirm"
                    self.selected=i; return ""
            if event.pos[1]>SCREEN_HEIGHT-70: return "back"
        if event.type == pygame.MOUSEMOTION:
            for i,r in enumerate(self._card_rects):
                if r.collidepoint(event.pos): self.selected=i; break
        return ""

    def get_skin(self) -> dict:
        return SKINS[self.selected]

    def draw(self, surface: pygame.Surface) -> None:
        self._pulse += 0.04
        surface.fill((14,16,26))
        for x in range(0,SCREEN_WIDTH,44):
            pygame.draw.line(surface,(22,25,36),(x,0),(x,SCREEN_HEIGHT))
        for y in range(0,SCREEN_HEIGHT,44):
            pygame.draw.line(surface,(22,25,36),(0,y),(SCREEN_WIDTH,y))
        title = self.assets.font("title_sm").render("Escolha seu Personagem",True,YELLOW)
        surface.blit(title,title.get_rect(center=(SCREEN_WIDTH//2,55)))
        self._card_rects=[]
        cols=5; card_w=136; card_h=158; gap=18
        total_w=cols*(card_w+gap)-gap
        sx_start=SCREEN_WIDTH//2-total_w//2; sy_start=110
        mouse=pygame.mouse.get_pos()
        for i,skin in enumerate(SKINS):
            col,row = i%cols, i//cols
            x = sx_start+col*(card_w+gap)
            y = sy_start+row*(card_h+gap+10)
            rect=pygame.Rect(x,y,card_w,card_h)
            self._card_rects.append(rect)
            hov = rect.collidepoint(mouse) or i==self.selected
            sel = i==self.selected
            bg_col=(55,60,80) if hov else (32,36,50)
            sh=rect.inflate(8,8)
            ss=pygame.Surface((sh.width,sh.height),pygame.SRCALPHA)
            pygame.draw.rect(ss,(0,0,0,90),ss.get_rect(),border_radius=14)
            surface.blit(ss,sh.topleft)
            pygame.draw.rect(surface,bg_col,rect,border_radius=12)
            if sel:
                t=math.sin(self._pulse)*0.5+0.5
                bc=tuple(int(c*0.7+255*0.3*t) for c in skin["primary"])
                for w in range(4,0,-1):
                    gs=pygame.Surface((rect.width+w*4,rect.height+w*4),pygame.SRCALPHA)
                    pygame.draw.rect(gs,(*bc,40*w),gs.get_rect(),w*2,border_radius=14)
                    surface.blit(gs,(rect.x-w*2,rect.y-w*2))
                pygame.draw.rect(surface,bc,rect,3,border_radius=12)
            elif hov:
                pygame.draw.rect(surface,(140,145,170),rect,2,border_radius=12)
            else:
                pygame.draw.rect(surface,(55,60,80),rect,1,border_radius=12)
            cx=rect.centerx; cy=rect.y+58
            r_out=30 if sel else 26
            pygame.draw.circle(surface,skin["secondary"],(cx,cy),r_out+3)
            pygame.draw.circle(surface,skin["primary"],  (cx,cy),r_out)
            pygame.draw.circle(surface,skin["accent"],   (cx,cy),r_out,2)
            hi=tuple(min(255,c+90) for c in skin["primary"])
            pygame.draw.circle(surface,hi,(cx-r_out//3,cy-r_out//3),r_out//3)
            pygame.draw.circle(surface,skin["accent"],(cx+8,cy),5)
            nm=self.assets.font("small").render(skin["name"],True,WHITE if not sel else YELLOW)
            surface.blit(nm,nm.get_rect(center=(cx,rect.bottom-32)))
            if sel:
                badge=self.assets.font("tiny").render("✔ SELECIONADO",True,(100,255,120))
                surface.blit(badge,badge.get_rect(center=(cx,rect.bottom-14)))
        hint=self.assets.font("tiny").render(
            "Setas para navegar  ·  Enter ou clique duplo para confirmar  ·  ESC para voltar",
            True,(110,115,140))
        surface.blit(hint,hint.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT-30)))


# ── Game Over / Vitória ───────────────────────────────────────────────────────

class GameOverScreen:
    def __init__(self, assets):
        self.assets      = assets
        self.score       = 0.0
        self.kills       = 0
        self.won         = False
        self.level       = 1
        self.state_name  = ""
        self._confetti   = [
            {"x":random.uniform(0,SCREEN_WIDTH),"y":random.uniform(-SCREEN_HEIGHT,0),
             "vy":random.uniform(80,200),"vx":random.uniform(-30,30),
             "color":SKINS[i%len(SKINS)]["primary"],"size":random.randint(5,11)}
            for i in range(80)
        ]
        self._last = None
        self._next_rect    = None
        self._retry_rect   = None
        self._menu_rect    = None

    def set_stats(self, score: float, kills: int,
                  won: bool, level: int, state_name: str) -> None:
        self.score      = score
        self.kills      = kills
        self.won        = won
        self.level      = level
        self.state_name = state_name

    def handle_event(self, event: pygame.event.Event) -> str:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN,pygame.K_SPACE,pygame.K_r): return "restart"
            if event.key == pygame.K_ESCAPE: return "menu"
            if self.won and event.key == pygame.K_n: return "next_level"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
            if self._next_rect  and self._next_rect.collidepoint(event.pos):  return "next_level"
            if self._retry_rect and self._retry_rect.collidepoint(event.pos): return "restart"
            if self._menu_rect  and self._menu_rect.collidepoint(event.pos):  return "menu"
        return ""

    def draw(self, surface: pygame.Surface) -> None:
        now = pygame.time.get_ticks()/1000.0
        dt  = 0.016 if self._last is None else min(0.05, now-self._last)
        self._last = now
        surface.fill((15,5,5) if not self.won else (5,15,5))
        if self.won:
            for c in self._confetti:
                c["x"]+=c["vx"]*dt; c["y"]+=c["vy"]*dt
                if c["y"]>SCREEN_HEIGHT:
                    c["y"]=-20; c["x"]=random.uniform(0,SCREEN_WIDTH)
                pygame.draw.rect(surface,c["color"],
                    (int(c["x"]),int(c["y"]),c["size"],c["size"]))
            t=math.sin(now*2)*0.5+0.5
            tc=(int(60+180*t),230,int(80+100*t))
            title=self.assets.font("title").render("VITÓRIA!",True,tc)
            sub  =self.assets.font("body").render(
                f"Nível {self.level-1} concluído  •  {self.state_name}",True,YELLOW)
        else:
            title=self.assets.font("title").render("ELIMINADO!",True,(255,70,70))
            sub  =self.assets.font("body").render("Sua trilha foi cortada.",True,(200,150,150))
        surface.blit(title,title.get_rect(center=(SCREEN_WIDTH//2,130)))
        surface.blit(sub,  sub.get_rect(center=(SCREEN_WIDTH//2,200)))
        s1=self.assets.font("body").render(f"Território: {self.score:.1f}%",True,YELLOW)
        s2=self.assets.font("body").render(f"Eliminações: {self.kills}",True,WHITE)
        surface.blit(s1,s1.get_rect(center=(SCREEN_WIDTH//2,268)))
        surface.blit(s2,s2.get_rect(center=(SCREEN_WIDTH//2,318)))
        if self.kills>=4:
            pred=self.assets.font("small").render("⚡ PREDADOR ⚡",True,(255,80,80))
            surface.blit(pred,pred.get_rect(center=(SCREEN_WIDTH//2,355)))
        mouse=pygame.mouse.get_pos(); btn_y=400
        if self.won:
            self._next_rect=pygame.Rect(0,0,230,52)
            self._next_rect.center=(SCREEN_WIDTH//2,btn_y)
            h=self._next_rect.collidepoint(mouse)
            pygame.draw.rect(surface,(30,120,55) if h else (20,80,38),self._next_rect,border_radius=10)
            pygame.draw.rect(surface,GREEN if h else (40,140,70),self._next_rect,2,border_radius=10)
            t=self.assets.font("body").render("Próximo Nível  ▶",True,GREEN if h else WHITE)
            surface.blit(t,t.get_rect(center=self._next_rect.center)); btn_y+=66
        self._retry_rect=pygame.Rect(0,0,230,50); self._retry_rect.center=(SCREEN_WIDTH//2,btn_y)
        h=self._retry_rect.collidepoint(mouse)
        pygame.draw.rect(surface,(55,100,55) if h else (40,60,40),self._retry_rect,border_radius=10)
        pygame.draw.rect(surface,YELLOW if h else (80,140,80),self._retry_rect,2,border_radius=10)
        surface.blit(self.assets.font("body").render("Jogar Novamente",True,YELLOW if h else WHITE),
            self.assets.font("body").render("Jogar Novamente",True,WHITE).get_rect(center=self._retry_rect.center))
        self._menu_rect=pygame.Rect(0,0,230,50); self._menu_rect.center=(SCREEN_WIDTH//2,btn_y+66)
        h=self._menu_rect.collidepoint(mouse)
        pygame.draw.rect(surface,(55,55,90) if h else (40,40,55),self._menu_rect,border_radius=10)
        pygame.draw.rect(surface,YELLOW if h else (90,90,130),self._menu_rect,2,border_radius=10)
        surface.blit(self.assets.font("body").render("Menu Principal",True,YELLOW if h else WHITE),
            self.assets.font("body").render("Menu Principal",True,WHITE).get_rect(center=self._menu_rect.center))
        hint_txt="N = próximo nível  ·  R = jogar  ·  ESC = menu" if self.won else "R = jogar novamente  ·  ESC = menu"
        hint=self.assets.font("tiny").render(hint_txt,True,(110,110,130))
        surface.blit(hint,hint.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT-30)))
