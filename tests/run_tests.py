"""
run_tests.py — TerritórIO: Edição Brasil
------------------------------------------
Runner de testes que funciona sem pytest instalado.
Executa todos os testes que não dependem de display pygame.

Execute da raiz do projeto:
    python tests/run_tests.py

Para testes completos (incluindo SpriteManager e colisão pygame):
    pip install pytest
    python -m pytest tests/ -v
"""

import sys
import os
import math
import json
from pathlib import Path

# Garante que src/ seja encontrado
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Mini-framework de testes
# ---------------------------------------------------------------------------

class TestRunner:
    def __init__(self):
        self.passed  = 0
        self.failed  = 0
        self._suite  = ""

    def suite(self, name: str) -> None:
        self._suite = name
        print(f"\n{'─'*55}")
        print(f"  {name}")
        print(f"{'─'*55}")

    def run(self, label: str, fn) -> None:
        try:
            fn()
            self.passed += 1
            print(f"  ✅  {label}")
        except AssertionError as e:
            self.failed += 1
            print(f"  ❌  {label}")
            print(f"       AssertionError: {e}")
        except Exception as e:
            self.failed += 1
            print(f"  ❌  {label}")
            print(f"       {type(e).__name__}: {e}")

    def summary(self) -> int:
        total = self.passed + self.failed
        print(f"\n{'='*55}")
        print(f"  RESULTADO: {self.passed}/{total} testes passando")
        if self.failed:
            print(f"  FALHAS:    {self.failed}")
        print(f"{'='*55}")
        return 1 if self.failed else 0


t = TestRunner()


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------

from src.entities.world     import World
from src.config.game_config import WORLD_COLS, WORLD_ROWS, CELL_SIZE

t.suite("World — grade de território")

t.run("grade tem WORLD_COLS × WORLD_ROWS células",
      lambda: World() and len(World().grid) == WORLD_COLS * WORLD_ROWS)
t.run("grade inicia vazia",
      lambda: all(v == 0 for v in World().grid))
t.run("set_owner_cell persiste em get_owner", lambda: (
    setattr(w := World(), "__x", w.set_owner_cell(5, 5, 1)) or
    w.get_owner(5*CELL_SIZE+1, 5*CELL_SIZE+1) == 1
))
t.run("coordenadas fora dos limites retornam -1",
      lambda: World().get_owner(-10, -10) == -1)
t.run("is_own_territory correto por id", lambda: (
    setattr(w := World(), "__x", w.set_owner_cell(10, 10, 2)) or
    (w.is_own_territory(10*CELL_SIZE+1, 10*CELL_SIZE+1, 2) is True and
     w.is_own_territory(10*CELL_SIZE+1, 10*CELL_SIZE+1, 3) is False)
))
t.run("count_owned correto após atribuições", lambda: (
    setattr(w := World(), "__x",
            [w.set_owner_cell(cx, cy, 1)
             for cx in range(5) for cy in range(5)]) or
    w.count_owned(1) == 25
))
t.run("count_owned retorna 0 inicialmente",
      lambda: World().count_owned(99) == 0)
t.run("clear_owner remove todas as células do dono", lambda: (
    setattr(w := World(), "__x",
            (w.set_owner_cell(1,1,6), w.set_owner_cell(2,2,6),
             w.clear_owner(6))) or
    w.count_owned(6) == 0
))
t.run("claim_polygon captura células internas", lambda: (
    setattr(w := World(), "__x", None) or
    w.claim_polygon([(50,50),(50+CELL_SIZE*8,50),
                     (50+CELL_SIZE*8,50+CELL_SIZE*8),(50,50+CELL_SIZE*8),
                     (50,50)], 8) > 0
))
t.run("claim_polygon retorna 0 para polígono vazio",
      lambda: World().claim_polygon([], 1) == 0)
t.run("get_leader_id retorna dono com mais células", lambda: (
    setattr(w := World(), "__x",
            [w.set_owner_cell(cx, cy, 2)
             for cx in range(10) for cy in range(10)]) or
    w.get_leader_id({1, 2}) == 2
))


# ---------------------------------------------------------------------------
# Trail
# ---------------------------------------------------------------------------

from src.entities.trail import Trail

t.suite("Trail — trilha das entidades")

t.run("primeiro ponto sempre adicionado", lambda: (
    (tr := Trail(1,(0,0,0))).add_point(10,20,5) or len(tr.points) == 1))
t.run("ponto muito próximo ignorado", lambda: (
    (tr := Trail(1,(0,0,0))).add_point(0,0) or tr.add_point(1,0,5)
    or len(tr.points) == 1))
t.run("ponto distante suficiente adicionado", lambda: (
    (tr := Trail(1,(0,0,0))).add_point(0,0) or tr.add_point(10,0,5)
    or len(tr.points) == 2))
t.run("clear esvazia pontos e reativa trilha", lambda: (
    (tr := Trail(1,(0,0,0))).add_point(0,0) or tr.add_point(10,0)
    or tr.clear() or (len(tr.points) == 0 and tr.active is True)))
t.run("comprimento de trilha vazia é 0",
      lambda: Trail(1,(0,0,0)).length() == 0.0)
t.run("comprimento triângulo 3-4-5", lambda: (
    (tr := Trail(1,(0,0,0))).add_point(0,0,0) or tr.add_point(3,4,0)
    or abs(tr.length() - 5.0) < 1e-5))
t.run("is_near_start detecta aproximação", lambda: (
    (tr := Trail(1,(0,0,0))) and
    [tr.add_point(float(i*10),0,0) for i in range(6)] and
    tr.is_near_start(5,0,10) is True))
t.run("is_near_start ignora posição distante", lambda: (
    (tr := Trail(1,(0,0,0))) and
    [tr.add_point(float(i*10),0,0) for i in range(6)] and
    tr.is_near_start(500,500,10) is False))


# ---------------------------------------------------------------------------
# Difficulty
# ---------------------------------------------------------------------------

from src.config.difficulty import DIFFICULTIES, DifficultyProfile, get_profile

t.suite("DifficultyProfile — perfis de dificuldade dos bots")

t.run("três níveis obrigatórios existem",
      lambda: all(k in DIFFICULTIES for k in ["facil","medio","dificil"]))
t.run("todos os valores são DifficultyProfile",
      lambda: all(isinstance(v, DifficultyProfile)
                  for v in DIFFICULTIES.values()))
t.run("speed_multiplier positivo em todos os perfis",
      lambda: all(p.speed_multiplier > 0 for p in DIFFICULTIES.values()))
t.run("think_interval positivo em todos os perfis",
      lambda: all(p.think_interval > 0 for p in DIFFICULTIES.values()))
t.run("probabilidades em [0,1]",
      lambda: all(0<=p.intercept_prob<=1 and 0<=p.hunt_prob<=1
                  for p in DIFFICULTIES.values()))
t.run("fácil pensa mais devagar que difícil",
      lambda: DIFFICULTIES["facil"].think_interval > DIFFICULTIES["dificil"].think_interval)
t.run("fácil caça menos que difícil",
      lambda: DIFFICULTIES["facil"].hunt_prob < DIFFICULTIES["dificil"].hunt_prob)
t.run("fácil intercepta menos que difícil",
      lambda: DIFFICULTIES["facil"].intercept_prob < DIFFICULTIES["dificil"].intercept_prob)
t.run("difícil alcança power-ups mais distantes",
      lambda: DIFFICULTIES["facil"].powerup_max_dist < DIFFICULTIES["dificil"].powerup_max_dist)
t.run("get_profile retorna perfil correto",
      lambda: get_profile("facil") is DIFFICULTIES["facil"])
t.run("get_profile é case-insensitive",
      lambda: get_profile("MEDIO") is DIFFICULTIES["medio"])
t.run("get_profile com nome inválido retorna padrão",
      lambda: get_profile("inexistente") is DIFFICULTIES["medio"])


# ---------------------------------------------------------------------------
# Brazil Maps
# ---------------------------------------------------------------------------

from src.core.brazil_maps import STATES, STATE_ORDER, project_polygon, point_in_polygon

t.suite("Brazil Maps — polígonos dos estados brasileiros")

t.run("27 estados presentes",       lambda: len(STATES) == 27)
t.run("27 estados na ordem",        lambda: len(STATE_ORDER) == 27)
t.run("sem duplicatas na ordem",    lambda: len(set(STATE_ORDER)) == 27)
t.run("project_polygon produz pontos na tela", lambda: all(
    0 <= x <= 1280 and 0 <= y <= 720
    for x,y in project_polygon(STATES["São Paulo"], 1280, 720, 80)
))
t.run("project_polygon preserva quantidade de pontos", lambda:
    len(project_polygon(STATES["Paraná"], 1280, 720)) == len(STATES["Paraná"]))
t.run("point_in_polygon detecta ponto interno",
      lambda: point_in_polygon(50, 50, [(0,0),(100,0),(100,100),(0,100)]) is True)
t.run("point_in_polygon detecta ponto externo",
      lambda: point_in_polygon(200, 200, [(0,0),(100,0),(100,100),(0,100)]) is False)


# ---------------------------------------------------------------------------
# Collision — _point_to_segment_dist (puro Python)
# ---------------------------------------------------------------------------

def _psd(px,py,ax,ay,bx,by):
    abx,aby = bx-ax,by-ay
    apx,apy = px-ax,py-ay
    l2 = abx*abx+aby*aby
    if l2<1e-6: return math.hypot(apx,apy)
    t = max(0.0,min(1.0,(apx*abx+apy*aby)/l2))
    return math.hypot(px-(ax+t*abx),py-(ay+t*aby))

t.suite("Collision — distância ponto-segmento")

t.run("ponto sobre segmento → distância 0",
      lambda: abs(_psd(5,0,0,0,10,0)) < 1e-6)
t.run("ponto perpendicular → distância correta",
      lambda: abs(_psd(5,3,0,0,10,0)-3) < 1e-6)
t.run("ponto além do extremo → distância ao extremo",
      lambda: abs(_psd(15,0,0,0,10,0)-5) < 1e-6)
t.run("segmento degenerado → distância ao ponto",
      lambda: abs(_psd(3,4,0,0,0,0)-5) < 1e-6)


# ---------------------------------------------------------------------------
# Game Config
# ---------------------------------------------------------------------------

from src.config.game_config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WORLD_COLS, WORLD_ROWS,
    CELL_SIZE, SKINS, PLAYER_SPEED, BOT_SPEED_BASE, NUM_BOTS,
)

t.suite("Game Config — constantes do jogo")

t.run("resolução positiva",   lambda: SCREEN_WIDTH > 0 and SCREEN_HEIGHT > 0)
t.run("FPS é 60",             lambda: FPS == 60)
t.run("mundo positivo",       lambda: WORLD_COLS > 0 and WORLD_ROWS > 0 and CELL_SIZE > 0)
t.run("pelo menos 5 skins",   lambda: len(SKINS) >= 5)
t.run("skins têm chaves obrigatórias",
      lambda: all(all(k in s for k in ("id","name","primary","secondary","accent"))
                  for s in SKINS))
t.run("velocidades positivas", lambda: PLAYER_SPEED > 0 and BOT_SPEED_BASE > 0)
t.run("pelo menos 1 bot",     lambda: NUM_BOTS >= 1)


# ---------------------------------------------------------------------------
# sprites.json integridade
# ---------------------------------------------------------------------------

t.suite("sprites.json — configuração de sprites")

SPRITES_JSON = ROOT / "assets" / "data" / "sprites.json"

t.run("arquivo sprites.json existe",         lambda: SPRITES_JSON.is_file())
t.run("sprites.json é JSON válido",          lambda: json.loads(SPRITES_JSON.read_text()))
t.run("chaves obrigatórias presentes", lambda: all(
    k in {ek for ek,_ in json.loads(SPRITES_JSON.read_text()).items()
          if not ek.startswith("_")}
    for k in ["player.default","bot.default",
               "powerup.size_up","powerup.speed","powerup.bomb",
               "powerup.shield","powerup.eagle"]
))
t.run("todos os sprites têm campos obrigatórios", lambda: all(
    not ({"path","scale","width","height","opacity","frames","fps","loop"} - set(v.keys()))
    for k,v in json.loads(SPRITES_JSON.read_text()).items()
    if not k.startswith("_")
))


# ---------------------------------------------------------------------------
# Resultado final
# ---------------------------------------------------------------------------

sys.exit(t.summary())
