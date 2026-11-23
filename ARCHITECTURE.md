# ARCHITECTURE.md — Paper.io 2: Edição Brasil

Documentação da arquitetura modular refatorada.

---

## Estrutura de diretórios

```
paperio2/
├── main.py                        Loop principal e máquina de estados
├── ARCHITECTURE.md                Este documento
├── requirements.txt               Dependências Python
│
├── assets/
│   ├── fonts/                     Kenney Future (.ttf) — CC0
│   ├── audio/                     SFX Kenney (.ogg) — CC0
│   ├── animations/                Futuras sequências de animação
│   ├── KENNEY_LICENSE.txt
│   └── sprites/
│       ├── player/                Sprites do jogador (PNG)
│       ├── bots/                  Sprites dos bots (PNG)
│       ├── powerups/              Ícones dos 5 power-ups (PNG)
│       ├── effects/               Efeitos visuais (PNG/spritesheet)
│       ├── backgrounds/           Fundos (PNG)
│       └── ui_kenney/             Botões e ícones Kenney (CC0)
│
└── src/
    ├── config/
    │   ├── game_config.py         Todas as constantes do jogo
    │   └── sprite_config.py       Configurações visuais de cada sprite
    │
    ├── core/
    │   ├── game.py                Núcleo da partida (GameSession)
    │   └── brazil_maps.py         Polígonos dos 27 estados brasileiros
    │
    ├── entities/
    │   ├── trail.py               Trilha deixada pelas entidades
    │   ├── world.py               Grade de território (ownership grid)
    │   ├── player.py              Entity base + Player (controlado)
    │   └── bot.py                 Bot com IA de 4 estados
    │
    ├── systems/
    │   ├── assets.py              Carregamento de fontes
    │   ├── audio.py               Carregamento e reprodução de SFX
    │   ├── camera.py              Câmera suave + zoom Eagle Eye
    │   ├── particles.py           Sistema de partículas visuais
    │   ├── collision.py           Detecção de colisões trilha→cabeça
    │   ├── powerups.py            Ciclo de vida dos power-ups
    │   └── sprite_manager.py      Carregamento e cache de sprites (CENTRAL)
    │
    └── ui/
        ├── hud.py                 HUD, ranking, minimapa, badge Predador
        └── menus.py               Menu, skin select, pausa, game over, vitória
```

---

## Responsabilidade de cada módulo

| Módulo | Responsabilidade |
|---|---|
| `main.py` | Inicialização, loop, máquina de estados, integração de sistemas |
| `config/game_config.py` | Todas as constantes (velocidade, tamanho, cores, skins) |
| `config/sprite_config.py` | Caminhos, escala, opacidade e animações de cada sprite |
| `core/game.py` | Partida: update, draw, colisões, power-ups, fim de jogo |
| `core/brazil_maps.py` | Polígonos geográficos dos 27 estados + projeção para pixels |
| `entities/trail.py` | Armazenamento de pontos da trilha + verificação de loop |
| `entities/world.py` | Grade de ownership, claim, contagem e flood fill |
| `entities/player.py` | Entity base, Player controlado, movimentação, renderização |
| `entities/bot.py` | IA com estados expand/return/hunt/evade, renderização |
| `systems/assets.py` | Carregamento de fontes Kenney com fallback para SysFont |
| `systems/audio.py` | SFX de arquivo (Kenney) + SFX procedurais (numpy) |
| `systems/camera.py` | Seguimento suave + offset de câmera |
| `systems/particles.py` | Partículas de burst, trilha capturada e morte |
| `systems/collision.py` | Detecção ponto-segmento, proteção de autocolisão e escudo |
| `systems/powerups.py` | Spawn, coleta, efeitos ativos, bomba, renderização |
| `systems/sprite_manager.py` | Cache de sprites, escala, fallback, animações |
| `ui/hud.py` | Barra superior, ranking, minimapa, badge, notificações |
| `ui/menus.py` | 5 telas de UI: menu, skin, pausa, game over, vitória |

---

## Fluxo de execução

```
main.py
│
├── pygame.init()
├── Assets(), AudioManager(), SpriteManager.preload()
├── MainMenu, SkinSelect, GameOverScreen, HUD
│
└── LOOP PRINCIPAL (60 FPS)
    │
    ├── STATE = menu       → MainMenu.handle_event / draw
    ├── STATE = select     → SkinSelect.handle_event / draw
    │
    ├── STATE = playing
    │   ├── GameSession.update(dt, keys)
    │   │   ├── Player.handle_input + speed *= pu_manager.speed_multiplier
    │   │   ├── Entity.update_position (todos)
    │   │   ├── Entity.update_trail_and_claim → World.claim_polygon
    │   │   ├── check_collisions → (killer, victim) pairs
    │   │   ├── PowerUpManager.update → coleta, efeitos, bomba
    │   │   ├── Entity.score_percent = World.ownership_percent
    │   │   ├── ParticleSystem.update
    │   │   └── Camera.follow
    │   └── GameSession.draw + HUD.draw
    │
    └── STATE = gameover   → GameOverScreen.handle_event / draw
```

---

## Comunicação entre módulos

```
main.py
  ↓ cria
GameSession ──uses──► World, Camera, ParticleSystem, PowerUpManager
  ↓ contém
[Player, Bot, ...] ──uses──► Trail, sprite_manager
  ↓ colisões via
collision.check_collisions(entities, player, shield)
  ↓ renderização via
GameSession.draw → Entity.draw(surface, offset) → sprite_manager.get(key)
  ↓ HUD via
HUD.draw(surface, session)
  ↓ power-ups via
PowerUpManager.draw_world + draw_hud
```

---

## Sistema de Sprites

### Como funciona

1. `sprite_config.py` define a chave e o caminho de cada sprite
2. `sprite_manager.get("chave")` carrega, processa e armazena em cache
3. Entidades chamam `sprite_manager.get("player.default")` ao renderizar
4. Se o arquivo não existir, o manager retorna um surface de fallback cinza
5. O jogo nunca trava por sprite ausente

### Como adicionar um novo sprite

**Passo 1** — Coloque o arquivo em `assets/sprites/<categoria>/meu_sprite.png`

**Passo 2** — Registre em `src/config/sprite_config.py`:
```python
"player.skin_nova": {
    "path":    "assets/sprites/player/nova_skin.png",
    "scale":   1.0,
    "width":   None,
    "height":  None,
    "opacity": 255,
    "frames":  1,
    "fps":     0,
    "loop":    False,
},
```

**Passo 3** — Use em qualquer lugar do código:
```python
from src.systems.sprite_manager import sprite_manager
sprite = sprite_manager.get("player.skin_nova")
surface.blit(sprite, (x, y))
```

Nenhum outro arquivo precisa ser modificado.

### Como substituir um sprite existente

Edite apenas o campo `"path"` em `sprite_config.py`. O cache é invalidado ao reiniciar.

Para forçar recarga em runtime (sem reiniciar):
```python
sprite_manager.invalidate("player.default")
```

### Como configurar dimensões e escala

```python
"meu_sprite": {
    "path":    "assets/sprites/player/sprite.png",
    "scale":   1.5,       # aplica escala uniforme
    "width":   48,        # força largura específica (anula scale.x)
    "height":  48,        # força altura específica (anula scale.y)
    "opacity": 200,       # 0 = transparente, 255 = opaco
}
```

### Como adicionar uma animação (spritesheet)

**Passo 1** — Crie um spritesheet horizontal: `sprite_N.png` onde N quadros ficam lado a lado.

**Passo 2** — Registre em `sprite_config.py`:
```python
"player.run": {
    "path":   "assets/sprites/player/run_sheet.png",
    "frames": 6,
    "fps":    12,
    "loop":   True,
    ...
}
```

**Passo 3** — Registre em `ANIMATION_CONFIG` em `sprite_config.py`:
```python
"player.run": {
    "sprite_key": "player.run",
    "frames": 6,
    "fps": 12,
    "loop": True,
}
```

**Passo 4** — Use em uma entidade:
```python
self._run_anim = sprite_manager.get_animation("player.run")

def update(self, dt):
    self._run_anim.update(dt)

def draw(self, surface, offset):
    surface.blit(self._run_anim.current, (sx, sy))
```

---

## Dependências entre sistemas

```
game_config   ← importado por todos os módulos (sem dependências)
sprite_config ← importado apenas por sprite_manager
sprite_manager← importado por player, bot, powerups
assets        ← importado por hud, menus, main
audio         ← importado por main
trail         ← importado por player (entity base)
world         ← importado por player, bot, game
player        ← importado por bot (herda Entity), game, collision
bot           ← importado por game
collision     ← importado por game
camera        ← importado por game
particles     ← importado por game
powerups      ← importado por game
brazil_maps   ← importado por game
hud           ← importado por main
menus         ← importado por main
```

Não há dependências circulares.

---

## Mecânicas preservadas

| Funcionalidade | Módulo responsável |
|---|---|
| Captura de território por polígono | `world.claim_polygon` |
| Autocolisão removida do jogador | `collision.check_collisions` |
| Escudo protege de trilhas inimigas | `collision.check_collisions` |
| Buff de velocidade nas bordas (×1.5, linger 1.5s) | `powerups.PowerUpManager` |
| 5 power-ups com timers independentes | `powerups.py` |
| Re-coleta reinicia timer (não acumula) | `ActiveEffect.reset()` |
| Bomba de Tinta (explosão circular real) | `game._bomb_claim` |
| Eagle Eye (zoom out 50% do mapa) | `game._draw_eagle_view` |
| IA de bots: 4 estados | `bot.update_ai` |
| Título Predador (4+ kills) + minimapa | `game.update` + `hud._draw_predator_badge` |
| Ranking em tempo real | `hud._draw_ranking` |
| 27 mapas dos estados brasileiros | `brazil_maps` + `game.GameSession.__init__` |
| Progressão por nível | `main.py` → `level += 1` |

---

## Executando o projeto

```bash
pip install pygame numpy
python main.py
```

Controles: `WASD` ou Setas · `P` pausa · `M` mute · `ESC` menu
