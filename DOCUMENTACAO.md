# PAPERWORLDS — Documentacao

**Versao:** 1.3.9  
**Historico:** ver [CHANGELOG.md](CHANGELOG.md)

## Visao geral

PAPERWORLDS e um jogo de captura de territorio inspirado em Paper.io, feito em Python com Pygame. O jogador traca trilhas, fecha areas e pinta o mapa. Bots disputam o mesmo espaco. Mapas usam o formato de estados brasileiros.

## Requisitos

- Python >= 3.9
- pygame >= 2.5

```bash
pip install pygame
python main.py
```

## Como jogar

- Setas ou WASD para mover (pode virar 180 e voltar pelo mesmo caminho).
- Saia da sua area, desenhe uma trilha e volte para conquistar o interior.
- Cortar a trilha de um inimigo elimina e pode transferir o territorio dele.
- A partida termina quando alguem pinta 100% da area jogavel.
- Player e bots renascem em espacos livres ate nao haver mais espaco valido ou alguem vencer.

## Ressurreicao (regra fixa)

Constantes em `src/config/game_config.py`:

| Constante | Valor | Significado |
|-----------|-------|-------------|
| `RESPAWN_CLEAR_RADIUS_CELLS` | 4 | Raio minimo de celulas **livres e jogaveis** exigido para renascer |
| `RESPAWN_SEED_RADIUS_CELLS` | 4 | Raio do territorio inicial apos o respawn |

O ponto de respawn so e aceito se o disco completo em torno dele estiver sem tinta. Se o mapa estiver saturado, `random_unowned_point` retorna `None` e o personagem nao renasce.

## Arquitetura

```
refactor/
  main.py                 # Loop principal, timestep fixo 60 Hz
  src/config/             # Constantes e dificuldade
  src/core/               # Partida, mapas BR
  src/entities/           # World, Player, Bot, Trail
  src/systems/            # Camera, colisao, audio, power-ups, particulas
  src/ui/                 # Menus e HUD
```

### Fluxo de uma partida

1. `GameSession` cria o mundo (mascara do estado), player e bots.
2. Cada tick (1/60 s): input, movimento + deslize, trilha/claim, colisoes, power-ups, camera.
3. Claim usa flood local + preenchimento de buracos (formato livre, tipo tinta).
4. Vitoria: `count_owned >= arena_cells`.

## Configuracoes principais

| Item | Valor |
|------|-------|
| FPS | 60 (passo fixo) |
| Mapa | 480 x 480 celulas (2880 px) |
| Celula | 6 px |
| Bots | 8 |
| Velocidade player | 155 |
| Velocidade base bot | 125 |

## Power-ups

Gerenciados por `PowerUpManager`: velocidade, escudo, visao de aguia, bomba de tinta, entre outros. A visao de aguia mantem o player no centro e desenha trilhas.

## IA dos bots

FSM com perfil de dificuldade (`difficulty.py`). O nivel da partida evolui o perfil (`evolve_for_level` / `promote_tier`). Bots podem reverter direcao e usar power-ups.

## Mapas brasileiros

`brazil_maps.py` projeta poligonos dos estados no mundo. A mascara `playable` limita movimento e conquista a area do estado.

## Salvamento

Arquivo `territorio_save.json`: high score, skin e nivel.

## Changelog resumido

Veja [CHANGELOG.md](CHANGELOG.md) para o historico completo (1.3.2 a 1.3.9).
