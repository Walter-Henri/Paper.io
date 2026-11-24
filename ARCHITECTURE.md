# ARCHITECTURE.md — TerritórIO: Edição Brasil

Documentação da arquitetura modular do projeto.  
**Versão:** `1.3.1` &nbsp;|&nbsp; [Histórico de alterações →](CHANGELOG.md)

---

## Estrutura de diretórios

```
territorIO/
├── main.py                        ← Ponto de entrada; loop principal; máquina de estados
├── iniciar.sh                     ← Instalação e inicialização automática (Ubuntu/Linux)
├── requirements.txt               ← Dependências Python
├── territorio_save.json           ← Criado automaticamente ao jogar
│
├── README.md                      ← Apresentação do projeto
├── ARCHITECTURE.md                ← Este documento
├── DOCUMENTACAO.md                ← Documentação técnica completa em português
├── CHANGELOG.md                   ← Histórico de versões e correções de bugs
│
├── assets/
│   ├── data/
│   │   └── sprites.json           ← Configuração externa de sprites (JSON) ⭐
│   ├── fonts/
│   │   ├── Kenney Future.ttf      ← Fonte principal (CC0)
│   │   └── Kenney Future Narrow.ttf
│   ├── audio/
│   │   └── *.ogg                  ← SFX Kenney (CC0)
│   ├── animations/                ← Spritesheets de animação (futuro)
│   └── sprites/
│       ├── players/               ← Sprites do jogador (PNG opcional)
│       ├── bots/                  ← Sprites dos bots (PNG opcional)
│       ├── powerups/              ← 5 ícones PNG gerados por código ⭐
│       │   ├── size_up.png
│       │   ├── speed.png
│       │   ├── bomb.png
│       │   ├── shield.png
│       │   └── eagle.png
│       ├── effects/               ← Efeitos visuais (PNG opcional)
│       ├── backgrounds/           ← Fundos (PNG opcional)
│       └── ui_kenney/             ← Botões e ícones Kenney (CC0)
│
├── src/
│   ├── config/
│   │   ├── game_config.py         ← Todas as constantes do jogo
│   │   ├── sprite_config.py       ← Configuração Python de fallback dos sprites
│   │   └── difficulty.py          ← Perfis de dificuldade dos bots ⭐
│   │
│   ├── core/
│   │   ├── game.py                ← Núcleo da partida (GameSession)
│   │   ├── brazil_maps.py         ← Polígonos dos 27 estados brasileiros
│   │   └── log_setup.py           ← Configuração centralizada de logging ⭐
│   │
│   ├── entities/
│   │   ├── trail.py               ← Trilha das entidades
│   │   ├── world.py               ← Grade de território (ownership grid)
│   │   ├── player.py              ← Entity base + Player controlado
│   │   └── bot.py                 ← IA com FSM de 6 estados ⭐
│   │
│   ├── systems/
│   │   ├── assets.py              ← Carregamento de fontes
│   │   ├── audio.py               ← SFX (arquivo + procedural via numpy)
│   │   ├── camera.py              ← Câmera suave + zoom Eagle Eye
│   │   ├── particles.py           ← Sistema de partículas visuais
│   │   ├── collision.py           ← Detecção de colisões trilha→cabeça
│   │   ├── powerups.py            ← Ciclo de vida dos power-ups
│   │   └── sprite_manager.py      ← Gerenciador centralizado de sprites ⭐
│   │
│   └── ui/
│       ├── hud.py                 ← HUD, ranking, minimapa, badge Predador
│       └── menus.py               ← 5 telas de interface
│
└── tests/
    ├── __init__.py
    ├── run_tests.py               ← Runner sem dependência de pytest (53 testes)
    ├── test_world.py              ← 11 testes para World
    ├── test_trail.py              ←  8 testes para Trail
    ├── test_difficulty.py         ← 10 testes para DifficultyProfile
    ├── test_collision.py          ←  8 testes para collision (requer pytest)
    └── test_sprite_manager.py     ← 12 testes para SpriteManager (requer pytest)
```

---

## Responsabilidade de cada módulo

| Módulo | Responsabilidade |
|---|---|
| `main.py` | Inicialização, loop 60 FPS, máquina de estados, integração de sistemas, encerramento seguro |
| `config/game_config.py` | Todas as constantes: resolução, velocidades, cores, skins, dimensões do mundo |
| `config/sprite_config.py` | Configuração Python de fallback dos sprites (usado quando JSON não carrega) |
| `config/difficulty.py` | Três perfis de dificuldade imutáveis (`facil`, `medio`, `dificil`) |
| `core/game.py` | Partida completa: update, draw, colisões, power-ups, fim de jogo |
| `core/brazil_maps.py` | Polígonos geográficos dos 27 estados + projeção lon/lat → pixels |
| `core/log_setup.py` | Configuração do módulo nativo `logging` (ativado com `--debug`) |
| `entities/trail.py` | Armazenamento de pontos da trilha, distância mínima, is_near_start |
| `entities/world.py` | Grade de ownership, claim_polygon, contagem, seed, clear |
| `entities/player.py` | Classe `Entity` base (com `radius` como `@property`) + `Player` controlado |
| `entities/bot.py` | IA com FSM de 6 estados e integração com `DifficultyProfile` |
| `systems/assets.py` | Fontes Kenney com fallback para SysFont |
| `systems/audio.py` | SFX de arquivo (.ogg) + SFX procedurais sintetizados via NumPy |
| `systems/camera.py` | Seguimento suave (lerp) + offset de câmera |
| `systems/particles.py` | Partículas de burst, trilha capturada e morte |
| `systems/collision.py` | Detecção ponto-segmento, autocolisão removida do jogador, proteção do escudo |
| `systems/powerups.py` | Spawn, coleta (jogador e bots), efeitos ativos, bomba, renderização |
| `systems/sprite_manager.py` | Carregamento via JSON externo, cache, fallback, escalonamento, animações |
| `ui/hud.py` | Barra superior, ranking em tempo real, painel de power-ups, Predador, notificações |
| `ui/menus.py` | Menu principal, skin select, pausa, game over, vitória |

---

## Fluxo de execução

```
python main.py [--debug]
│
├── configure_logging(debug)          ← log_setup.py
├── pygame.init() + mixer.init()
├── Assets(), AudioManager()
├── sprite_manager.preload([...])     ← carrega JSON + sprites em cache
├── MainMenu, SkinSelect, GameOverScreen, HUD
│
└── LOOP PRINCIPAL — clock.tick_busy_loop(60)
    │
    ├── dt = raw_dt clampeado a MAX_DT
    │
    ├── EVENTOS pygame.event.get()
    │   ├── QUIT → _write_save() → _quit() → sys.exit(0)
    │   ├── K_F4 + KMOD_ALT → mesmo caminho acima
    │   ├── K_m → audio.toggle()
    │   └── eventos por estado (menu/select/playing/gameover)
    │
    ├── UPDATE por estado
    │   ├── menu      → MainMenu.update(dt)
    │   ├── select    → (passivo)
    │   ├── playing   → GameSession.update(dt, keys)
    │   │               ├── Player.handle_input + speed *= pu_manager.speed_multiplier
    │   │               ├── Bot.update_ai(dt, world, entities, powerup_items)
    │   │               │   └── FSM: evade → return → collect_pu → intercept → hunt → expand
    │   │               ├── Entity.update_position (todos)
    │   │               ├── Entity.update_trail_and_claim → World.claim_polygon
    │   │               ├── collision.check_collisions(entities, player, shield)
    │   │               ├── PowerUpManager.update(dt, ..., bots, bot_bomb_callback)
    │   │               │   ├── coleta pelo jogador → _apply()
    │   │               │   └── coleta por bots → _apply_to_bot()
    │   │               ├── PowerUpManager.update_bot_effects(dt, bots)
    │   │               ├── Entity.score_percent = World.ownership_percent
    │   │               ├── ParticleSystem.update(dt)
    │   │               └── Camera.follow(player.x, player.y, lerp)
    │   └── gameover  → (passivo)
    │
    ├── DRAW por estado
    │   ├── menu      → MainMenu.draw(screen)
    │   ├── select    → SkinSelect.draw(screen)
    │   ├── playing   → GameSession.draw(screen, assets, paused)
    │   │               └── HUD.draw(screen, session, paused)
    │   └── gameover  → GameOverScreen.draw(screen)
    │
    └── pygame.display.flip()
```

---

## Comunicação entre módulos

```
main.py
  │ cria
  ├─► Assets, AudioManager, sprite_manager (global)
  ├─► MainMenu, SkinSelect, GameOverScreen, HUD
  └─► GameSession(skin, level)
        │ contém
        ├─► World
        ├─► Camera
        ├─► ParticleSystem
        ├─► PowerUpManager(world_w, world_h)
        ├─► Player(x, y, skin)  ──────────────► Trail, sprite_manager
        └─► [Bot(x, y, skin, difficulty_profile)]
              │                                  Trail, sprite_manager
              └─► DifficultyProfile (somente leitura)

GameSession.update()
  ├─► Bot.update_ai(dt, world, entities, powerup_items)
  ├─► Entity.update_position(dt)
  ├─► Entity.update_trail_and_claim(world) ──► World.claim_polygon
  ├─► collision.check_collisions(entities, player, shield_active)
  ├─► PowerUpManager.update(..., bots, bot_bomb_callback)
  └─► PowerUpManager.update_bot_effects(dt, bots)

GameSession.draw()
  ├─► Entity.draw(surface, camera_offset) ──► sprite_manager.get(key)
  ├─► PowerUpManager.draw_world(surface, ox, oy)
  └─► HUD.draw(surface, session, paused)
        ├─► PowerUpManager.draw_hud(...)
        ├─► _draw_predator_badge()
        └─► _draw_minimap(session)
```

---

## Hierarquia de classes das entidades

```
Entity  (src/entities/player.py)
│   ├── id, x, y, color, speed, direction
│   ├── trail: Trail
│   ├── alive, outside, drawing, kills, score_percent
│   ├── @property radius → PLAYER_RADIUS   ← adicionado em v1.3.1
│   ├── set_direction(dx, dy)              ← sem reversão de 180°
│   ├── update_position(dt)
│   ├── update_trail_and_claim(world)
│   ├── kill()
│   └── draw(surface, camera_offset)
│
├── Player(Entity)  (src/entities/player.py)
│   ├── skin_id, skin_name
│   └── handle_input(keys)
│
└── Bot(Entity)  (src/entities/bot.py)
    ├── _profile: DifficultyProfile
    ├── difficulty: float
    ├── state: str  ("expand"|"return"|"collect_pu"|"intercept"|"hunt"|"evade")
    ├── bot_effects: dict
    ├── update_ai(dt, world, entities, powerup_items)
    ├── _do_expand / _do_return / _do_evade
    ├── _best_powerup(items, entities) → utilidade
    ├── _find_hunt_target / _find_intercept
    ├── _assess_danger / _threat_direction
    ├── _steer_to / _strategic_turn / _best_direction_toward_own
    ├── _force_unstick
    └── draw(surface, camera_offset)
```

---

## Sistema de Sprites

### Pipeline de carregamento

```
assets/data/sprites.json          ← fonte primária (JSON externo)
         │  falha/ausente
         ▼
src/config/sprite_config.py       ← fonte secundária (Python fallback)
         │
         ▼
SpriteManager._load_surface(path, cfg)
         │  arquivo não encontrado ou corrompido
         ▼
SpriteManager._get_fallback()     ← círculo cinza 28×28 px (nunca trava o jogo)
         │
         ▼
SpriteManager._cache[key]         ← armazenado; reutilizado em chamadas seguintes
```

### Como adicionar um sprite (3 passos)

**1.** Coloque o PNG em `assets/sprites/<categoria>/meu_sprite.png`

**2.** Registre em `assets/data/sprites.json`:
```json
"player.skin_nova": {
    "descricao": "Minha skin personalizada",
    "path":      "assets/sprites/players/meu_sprite.png",
    "scale":     1.0,
    "width":     null,
    "height":    null,
    "opacity":   255,
    "frames":    1,
    "fps":       0,
    "loop":      false,
    "categoria": "player"
}
```

**3.** Use em qualquer módulo:
```python
from src.systems.sprite_manager import sprite_manager
surf = sprite_manager.get("player.skin_nova")
surface.blit(surf, (x, y))
```

Nenhum outro arquivo precisa ser alterado.

### Métodos públicos do SpriteManager

| Método | Descrição |
|---|---|
| `get(key)` | Retorna Surface do sprite; usa cache; fallback se ausente |
| `get_scaled(key, w, h)` | Retorna Surface redimensionada; cache por dimensão |
| `get_animation(key)` | Retorna `AnimationState` para sprites animados |
| `preload(keys)` | Pré-carrega lista de sprites antes do loop principal |
| `invalidate(key)` | Remove do cache (força recarregamento) |
| `reload_config()` | Relê JSON e limpa cache (hot-reload em desenvolvimento) |
| `list_sprites(categoria)` | Lista chaves registradas, com filtro opcional |

---

## Sistema de Dificuldade dos Bots

Cada partida distribui os 8 bots em três perfis:

```
Partida (8 bots)
├── 2 bots com DifficultyProfile("facil")
│       think_interval=0.55s, hunt_prob=12%, intercept_prob=8%
├── 4 bots com DifficultyProfile("medio")
│       think_interval=0.32s, hunt_prob=28%, intercept_prob=22%
└── 2 bots com DifficultyProfile("dificil")
        think_interval=0.14s, hunt_prob=45%, intercept_prob=40%
```

A diferença está na **qualidade das decisões**, não em velocidade artificial:
- Bots difíceis reavaliam 7× por segundo vs 2× por segundo dos fáceis
- Bots difíceis preveem 4 passos à frente na interceptação vs 1 passo dos fáceis
- Bots difíceis buscam power-ups até 260 px de distância vs 110 px dos fáceis

---

## Grafo de dependências (sem circulares)

```
game_config    ←── todos os módulos
sprite_config  ←── sprite_manager (fallback)
difficulty     ←── bot, game
log_setup      ←── main
trail          ←── player
world          ←── player, bot, game
player         ←── bot (herda Entity), game, collision
bot            ←── game
collision      ←── game
camera         ←── game
particles      ←── game
powerups       ←── game
brazil_maps    ←── game
sprite_manager ←── player, bot, powerups
assets         ←── hud, menus, main
audio          ←── main
hud            ←── main
menus          ←── main
```

---

## Correções de bugs por versão

| Versão | Bug | Arquivo | Correção |
|---|---|---|---|
| **1.3.1** | `AttributeError: 'Bot' object has no attribute 'radius'` | `entities/player.py` | Adicionado `@property radius` na classe `Entity` |

---

## Executando o projeto

```bash
# Ubuntu/Linux (recomendado — cria venv automaticamente)
chmod +x iniciar.sh && ./iniciar.sh

# Manual (qualquer SO)
pip install pygame>=2.5.0 numpy>=1.24.0
python main.py

# Com logging verbose
python main.py --debug

# Testes (sem pytest)
python tests/run_tests.py

# Testes completos (com pytest)
pip install pytest && python -m pytest tests/ -v
```

**Controles:** `WASD` / Setas → mover &nbsp;|&nbsp; `P` → pausar &nbsp;|&nbsp; `M` → mute &nbsp;|&nbsp; `ESC` → menu
