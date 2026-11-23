# Paper.io 2 — Edição Brasil
## Documentação Completa do Projeto

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Requisitos e Instalação](#2-requisitos-e-instalação)
3. [Como Jogar](#3-como-jogar)
4. [Arquitetura do Projeto](#4-arquitetura-do-projeto)
5. [Módulos em Detalhe](#5-módulos-em-detalhe)
6. [Sistema de Power-ups](#6-sistema-de-power-ups)
7. [Inteligência Artificial dos Bots](#7-inteligência-artificial-dos-bots)
8. [Modo Predador](#8-modo-predador)
9. [Mapas dos Estados Brasileiros](#9-mapas-dos-estados-brasileiros)
10. [Sistema de Sprites](#10-sistema-de-sprites)
11. [Sistema de Áudio](#11-sistema-de-áudio)
12. [Progressão e Salvamento](#12-progressão-e-salvamento)
13. [Como Expandir o Jogo](#13-como-expandir-o-jogo)
14. [Referência de Configurações](#14-referência-de-configurações)

---

## 1. Visão Geral

**Paper.io 2 — Edição Brasil** é um jogo de captura de território inspirado em Paper.io 2, desenvolvido em Python com Pygame. O jogador controla um personagem que traça trilhas no mapa e fecha loops para conquistar área. O objetivo é dominar o maior território possível eliminando oponentes e sobrevivendo.

### Destaques
- 27 mapas únicos baseados nos estados brasileiros reais
- Sistema completo de 5 power-ups com sprites próprios
- IA de bots com 6 estados comportamentais e avaliação de utilidade
- Bots coletam power-ups ativamente e usam bomba de tinta
- Modo Predador com radar tático, estatísticas e minimapa aprimorado
- Arquitetura modular com gerenciador centralizado de sprites
- Progressão por nível com salvamento automático

---

## 2. Requisitos e Instalação

### Dependências
```
Python  >= 3.9
pygame  >= 2.5.0
numpy   >= 1.24.0
```

### Instalação
```bash
# Instalar dependências
pip install pygame numpy

# Executar o jogo
python main.py
```

### Estrutura de diretórios
```
paperio2/
├── main.py                        ← Ponto de entrada
├── ARCHITECTURE.md                ← Documentação de arquitetura
├── DOCUMENTACAO.md                ← Esta documentação
├── requirements.txt
├── paperio_save.json              ← Criado automaticamente ao jogar
│
├── assets/
│   ├── fonts/                     ← Kenney Future (.ttf) — CC0
│   ├── audio/                     ← SFX Kenney (.ogg) — CC0
│   ├── animations/                ← Futuras sequências de animação
│   └── sprites/
│       ├── player/                ← Sprites do jogador (opcional)
│       ├── bots/                  ← Sprites dos bots (opcional)
│       ├── powerups/              ← 5 ícones PNG gerados automaticamente
│       ├── effects/               ← Efeitos visuais (opcional)
│       ├── backgrounds/           ← Fundos (opcional)
│       └── ui_kenney/             ← Botões e ícones Kenney (CC0)
│
└── src/
    ├── config/
    │   ├── game_config.py         ← Todas as constantes do jogo
    │   └── sprite_config.py       ← Configurações de sprites e animações
    ├── core/
    │   ├── game.py                ← Núcleo da partida
    │   └── brazil_maps.py         ← Polígonos dos 27 estados
    ├── entities/
    │   ├── trail.py               ← Trilha das entidades
    │   ├── world.py               ← Grade de território
    │   ├── player.py              ← Jogador controlado
    │   └── bot.py                 ← IA dos bots
    ├── systems/
    │   ├── assets.py              ← Fontes tipográficas
    │   ├── audio.py               ← Efeitos sonoros
    │   ├── camera.py              ← Câmera e zoom
    │   ├── particles.py           ← Partículas visuais
    │   ├── collision.py           ← Detecção de colisões
    │   ├── powerups.py            ← Gerenciamento de power-ups
    │   └── sprite_manager.py      ← Carregamento e cache de sprites
    └── ui/
        ├── hud.py                 ← HUD, minimapa, badge Predador
        └── menus.py               ← 5 telas de interface
```

---

## 3. Como Jogar

### Controles

| Ação | Tecla |
|---|---|
| Mover para cima | ↑ ou W |
| Mover para baixo | ↓ ou S |
| Mover para a esquerda | ← ou A |
| Mover para a direita | → ou D |
| Pausar / continuar | P |
| Mute / desmute | M |
| Voltar ao menu | ESC |

### Mecânicas básicas

**Capturar território:**
1. Mova-se para fora do seu território (colorido com sua cor)
2. Uma trilha é traçada enquanto você está fora
3. Volte ao seu território para fechar o loop — a área interior é conquistada
4. Quanto maior a área fechada, mais território você ganha

**Eliminar oponentes:**
- Atravesse a trilha de um inimigo enquanto ele está fora do próprio território
- O inimigo é eliminado e perde todo o território que havia conquistado

**Ser eliminado:**
- Se um inimigo atravessar SUA trilha enquanto você está fora do seu território
- Você perde imediatamente (sem segunda chance, exceto com Escudo ativo)

**Buff de borda:**
- Ao encostar em qualquer borda do mapa, você recebe velocidade ×1.5
- O efeito persiste por 1.5 segundos após sair da borda
- Combina com o power-up Turbo (resultado: ×3.0)

### Condição de vitória
- Eliminar todos os bots adversários, **ou**
- Conquistar 100% do território jogável

---

## 4. Arquitetura do Projeto

### Fluxo de execução
```
main.py
 └── Loop principal (60 FPS)
      ├── Eventos de teclado/mouse
      ├── Update por estado:
      │    menu → MainMenu.update()
      │    select → SkinSelect (passivo)
      │    playing → GameSession.update(dt, keys)
      │    gameover → GameOverScreen (passivo)
      └── Draw por estado:
           menu → MainMenu.draw()
           select → SkinSelect.draw()
           playing → GameSession.draw() + HUD.draw()
           gameover → GameOverScreen.draw()
```

### Máquina de estados
```
[menu] ──"jogar"──► [select] ──"confirmar"──► [playing]
  ▲                    │ "voltar"               │  │
  │                    ▼                        │  │
  │                  [menu]          "eliminou"─┘  │ "venceu"
  │                                                 │
  └────────────"menu"──────── [gameover] ◄──────────┘
                                   │ "próximo nível"
                                   └──► [playing] (novo nível)
```

### Comunicação entre módulos
```
main.py          cria e orquestra todos
GameSession      integra World + Camera + ParticleSystem + PowerUpManager + Entities
Player / Bot     usam Trail, World (para territórios) e sprite_manager (visuais)
collision        recebe lista de entidades, retorna pares (killer, victim)
PowerUpManager   gerencia itens, efeitos do jogador e dos bots
HUD              lê dados do GameSession sem modificar estado
menus.py         eventos de UI → retornam strings de ação para main.py
```

---

## 5. Módulos em Detalhe

### `src/config/game_config.py`
Único arquivo de constantes. Altere aqui para ajustar qualquer parâmetro:

| Constante | Padrão | Descrição |
|---|---|---|
| `SCREEN_WIDTH / HEIGHT` | 1280 × 720 | Resolução da janela |
| `WORLD_COLS / ROWS` | 240 × 240 | Dimensões da grade |
| `CELL_SIZE` | 6 px | Tamanho de cada célula |
| `PLAYER_SPEED` | 155.0 | Velocidade base do jogador |
| `BOT_SPEED_BASE` | 125.0 | Velocidade base dos bots |
| `NUM_BOTS` | 8 | Quantidade de bots por partida |
| `AI_HUNT_RANGE` | 160 px | Alcance de caça dos bots |
| `AI_DANGER_RANGE` | 90 px | Distância de detecção de perigo |
| `KILL_RADIUS` | 11 px | Raio de colisão fatal |

### `src/core/game.py` — GameSession
Responsável por uma partida completa. Principais métodos:

```python
GameSession(skin, level)   # inicia partida
session.update(dt, keys)   # atualiza toda a lógica
session.draw(surface, assets, paused)  # renderiza o mundo
```

Internamente gerencia:
- Spawn de jogador e bots em posições não sobrepostas
- Loop de update: input → posição → trilha → colisões → power-ups → câmera
- Condições de vitória/derrota
- Callback da bomba de tinta (jogador e bots)

### `src/entities/world.py` — World
Grade de ownership em memória (`list[int]`). Cada célula guarda o `id` do dono.

```python
world.get_owner(x, y)                   # retorna id do dono
world.is_own_territory(x, y, owner_id) # True se célula é do dono
world.claim_polygon(points, owner_id)   # reivindica área pelo polígono da trilha
world.ownership_percent(owner_id)       # % da grade pertencente ao dono
world.set_owner_cell(cx, cy, owner_id)  # força uma célula
world.clear_owner(owner_id)             # libera todas as células do dono
```

### `src/systems/collision.py`
Detecta colisões entre cabeças e segmentos de trilha usando distância ponto-segmento.

Regras especiais implementadas:
- **Jogador não morre pela própria trilha** (autocolisão removida)
- **Escudo ativo protege** o jogador de qualquer colisão externa
- Bots mantêm autocolisão com imunidade parcial (últimos `SELF_IMMUNITY_POINTS` segmentos)

---

## 6. Sistema de Power-ups

### Os 5 power-ups

| Ícone | Nome | Tecla visual | Duração | Efeito |
|---|---|---|---|---|
| 🟠 | **EXPANSÃO** | Setas para fora | 4 s | Dobra raio e trilha |
| 🔵 | **TURBO** | Raio | 3 s | Dobra velocidade |
| 🔴 | **BOMBA** | Explosão | Instantâneo | Conquista área circular de 90 px |
| 🟢 | **ESCUDO** | Hexágono | 3 s | Imunidade a eliminações |
| 🟣 | **VISÃO** | Olho | 5 s | Zoom out mostrando 50% do mapa |

### Regras de coleta
- Itens surgem aleatoriamente a cada **5 segundos** (máximo 6 itens simultâneos)
- Coleta por contato (distância < raio do personagem + raio do item)
- **Re-coleta reinicia o timer**, nunca acumula duração
- Efeitos simultâneos compatíveis se forem de tipos diferentes
- **Bots também coletam power-ups** e usam a bomba estrategicamente

### Buff de borda (passivo)
- Velocidade ×1.5 ao tocar qualquer borda do mapa
- Persiste **1.5 segundos** após sair da borda
- Combina multiplicativamente com Turbo: ×1.5 × ×2.0 = ×3.0

### HUD dos efeitos ativos
No canto inferior esquerdo, cada efeito ativo exibe:
- Nome do efeito (cor característica)
- Barra de progresso de duração
- Tempo restante em segundos

---

## 7. Inteligência Artificial dos Bots

Os bots usam um sistema de **avaliação de utilidade** com 6 estados. A cada intervalo de reavaliação (varia com a dificuldade), o bot avalia qual estado maximiza seu benefício.

### Os 6 estados

| Estado | Prioridade | Comportamento |
|---|---|---|
| `evade` | 1ª (sobrevivência) | Foge para o próprio território quando inimigo ameaça a trilha |
| `return` | 2ª (auto-preservação) | Volta ao território quando a trilha é longa demais |
| `collect_pu` | 3ª (oportunismo) | Desvia para coletar power-up próximo se for lucrativo |
| `intercept` | 4ª (ofensivo) | Prevê posição futura do inimigo e corta o caminho |
| `hunt` | 5ª (ofensivo) | Mira o meio da trilha exposta de um inimigo |
| `expand` | 6ª (padrão) | Captura território de forma estratégica |

### Coleta de power-ups pelos bots

Os bots avaliam cada power-up disponível por:
- **Distância** (máximo configurável por dificuldade)
- **Tipo** vs estado atual (cada estado tem uma lista de prioridades de tipos)
- **Risco** (penalidade se a trilha está muito exposta)

Tabela de prioridade de tipo por estado:

| Estado | 1º | 2º | 3º | 4º | 5º |
|---|---|---|---|---|---|
| expand | BOMBA | TURBO | EXPANSÃO | ESCUDO | VISÃO |
| hunt | TURBO | EXPANSÃO | BOMBA | ESCUDO | VISÃO |
| intercept | TURBO | BOMBA | EXPANSÃO | ESCUDO | VISÃO |
| evade | ESCUDO | TURBO | VISÃO | BOMBA | EXPANSÃO |
| return | ESCUDO | TURBO | VISÃO | BOMBA | EXPANSÃO |

### Variáveis de dificuldade

Cada bot recebe uma `difficulty` de 0.7 a 1.4 (aleatória por partida).

| Fator | Efeito da dificuldade alta |
|---|---|
| Velocidade | +30% sobre a base |
| Intervalo de reavaliação | Mais frequente (pensa mais rápido) |
| Alcance de caça | Maior |
| Previsão de interceptação | Mais passos à frente |
| Max. trilha antes de retornar | Maior (mais corajoso) |
| Probabilidade de hunt/intercept | Maior |

### Anti-stuck
Se o bot não se mover mais de 2 px entre reavaliações consecutivas, ativa o mecanismo anti-stuck: tenta uma direção perpendicular, depois uma aleatória não reversa.

### Indicador visual de estado
Um pequeno ponto colorido acima de cada bot indica o estado atual:
- Cinza = expand · Azul = return · Verde-água = collect_pu
- Vermelho = hunt · Laranja = intercept · Amarelo = evade

---

## 8. Modo Predador

Desbloqueado ao eliminar **4 ou mais adversários** em uma partida.

### Componentes visuais

**Badge animada** (centro superior da tela):
- Texto "⚡ PREDADOR ⚡" com cor pulsante em vermelho
- Glow exterior animado em 4 camadas
- Fundo semi-transparente com borda dinâmica

**Radar tático** (canto inferior direito):
- Minimapa de 150×150 px com território de todos os jogadores
- Linha de varredura giratória (efeito de radar)
- Power-ups no minimapa com cores características
- Jogador: círculo branco com anel pulsante
- Bots: círculo colorido com borda indicando o estado atual
  - Vermelho = hunt / intercept (agressivo)
  - Amarelo = evade (fugindo)
  - Verde-água = collect_pu (coletando item)

**Painel de estatísticas** (esquerda do radar):
- Kills do jogador
- % de território atual
- Lista de bots vivos com nome, % de área e estado atual

### Como o Predador impacta a jogabilidade
O modo Predador é puramente informacional — não aumenta poder de ataque nem velocidade. O benefício é **informação tática**: saber onde estão todos os inimigos e em que estado a IA de cada bot se encontra.

---

## 9. Mapas dos Estados Brasileiros

A progressão segue esta ordem de estados por nível:

| Nível | Estado | | Nível | Estado |
|---|---|---|---|---|
| 1 | São Paulo | | 15 | Mato Grosso do Sul |
| 2 | Rio de Janeiro | | 16 | Rio Grande do Norte |
| 3 | Minas Gerais | | 17 | Paraíba |
| 4 | Bahia | | 18 | Espírito Santo |
| 5 | Rio Grande do Sul | | 19 | Piauí |
| 6 | Paraná | | 20 | Alagoas |
| 7 | Santa Catarina | | 21 | Rondônia |
| 8 | Pernambuco | | 22 | Tocantins |
| 9 | Ceará | | 23 | Sergipe |
| 10 | Goiás | | 24 | Amapá |
| 11 | Pará | | 25 | Roraima |
| 12 | Maranhão | | 26 | Acre |
| 13 | Amazonas | | 27 | Distrito Federal |
| 14 | Mato Grosso | | 28+ | Reinicia do nível 1 |

Os polígonos são armazenados em coordenadas geográficas (lon, lat) e projetados para pixels via `project_polygon()` com margem de 80 px para manter o mapa grande na tela.

---

## 10. Sistema de Sprites

### Funcionamento

```
sprite_config.py    define chave + caminho + parâmetros visuais
      ↓
sprite_manager.py   carrega, processa e armazena em cache
      ↓
player.py / bot.py / powerups.py   chamam sprite_manager.get("chave")
```

Se o arquivo de sprite não existir, o manager retorna um surface de fallback cinza. O jogo nunca trava por sprite ausente.

### Adicionar um sprite novo (3 passos)

**1.** Coloque o arquivo PNG em `assets/sprites/<categoria>/meu_sprite.png`

**2.** Registre em `src/config/sprite_config.py`:
```python
"jogador.skin_nova": {
    "path":    "assets/sprites/player/nova_skin.png",
    "scale":   1.0,       # multiplicador de escala
    "width":   None,      # largura final (None = usa scale)
    "height":  None,      # altura final  (None = usa scale)
    "opacity": 255,       # 0–255
    "frames":  1,         # 1 = estático
    "fps":     0,         # quadros/segundo para animação
    "loop":    False,     # True = loop contínuo
},
```

**3.** Use em qualquer lugar:
```python
from src.systems.sprite_manager import sprite_manager

sprite = sprite_manager.get("jogador.skin_nova")
surface.blit(sprite, (x, y))

# Com dimensões específicas:
sprite = sprite_manager.get_scaled("jogador.skin_nova", 48, 48)
```

### Substituir sprite existente
Apenas edite o campo `"path"` em `sprite_config.py`. O cache é limpo automaticamente ao reiniciar.

Para forçar recarga sem reiniciar:
```python
sprite_manager.invalidate("chave.do.sprite")
```

### Adicionar animação por spritesheet

**1.** Crie um spritesheet horizontal: N quadros lado a lado em um PNG.

**2.** Em `sprite_config.py`, configure `frames`, `fps` e `loop`.

**3.** Em `ANIMATION_CONFIG`, registre a animação:
```python
"jogador.correndo": {
    "sprite_key": "jogador.skin_corrida",
    "frames": 8,
    "fps": 12,
    "loop": True,
}
```

**4.** Na entidade:
```python
self._anim = sprite_manager.get_animation("jogador.correndo")

def update(self, dt):
    self._anim.update(dt)

def draw(self, surface, offset):
    surface.blit(self._anim.current, (sx, sy))
```

---

## 11. Sistema de Áudio

### Sons disponíveis

| Chave | Fonte | Descrição |
|---|---|---|
| `click` | Kenney CC0 | Clique de botão |
| `click2` | Kenney CC0 | Variante de clique |
| `switch` | Kenney CC0 | Troca de seleção |
| `tap` | Kenney CC0 | Toque suave |
| `claim` | Procedural | Captura de território |
| `claim2` | Procedural | Harmônico de captura |
| `death` | Procedural | Eliminação do jogador |
| `kill` | Procedural | Eliminou um inimigo |
| `start` | Procedural | Início de partida |
| `victory` | Procedural | Vitória |

### Adicionar um som
1. Coloque o `.ogg` em `assets/audio/`
2. Em `src/systems/audio.py`, adicione ao dicionário `file_sounds`:
   ```python
   "nome_chave": "nome_do_arquivo.ogg",
   ```
3. Use em qualquer lugar: `audio.play("nome_chave")`

---

## 12. Progressão e Salvamento

### Salvamento automático
O arquivo `paperio_save.json` é criado/atualizado automaticamente ao:
- Vencer uma partida
- Ser eliminado

Conteúdo salvo:
```json
{
  "high_score": 42.7,
  "skin_id": 3,
  "level": 5
}
```

### Progressão de nível
- **Vitória** → `level += 1`, novo mapa no próximo nível
- **Derrota** → permanece no mesmo nível
- Após o nível 27 (Distrito Federal), reinicia do nível 1 (São Paulo) com os mesmos bots

---

## 13. Como Expandir o Jogo

### Adicionar um novo power-up

**1.** Em `src/systems/powerups.py`, defina o identificador e adicione ao `POWERUP_DEFS`:
```python
PU_MEU_ITEM = "MEU_ITEM"
POWERUP_DEFS["MEU_ITEM"] = {
    "duration": 5.0,
    "color": (200, 100, 255),
    "label": "MEU ITEM",
    "sprite": "powerup.meu_item",
}
```

**2.** Em `sprite_config.py`, registre o sprite.

**3.** Em `PowerUpManager._apply()`, adicione o efeito:
```python
if kind == PU_MEU_ITEM:
    # aplica o efeito
    pass
```

**4.** Em `game.py` ou `player.py`, aplique o modificador durante o update.

### Adicionar um novo estado ao bot

Em `src/entities/bot.py`, no método `update_ai()`:
```python
# Adicione antes do expand
if minha_condicao:
    self.state = "meu_estado"
    self._do_meu_estado(world, entities)
    return
```

Implemente `_do_meu_estado()` e adicione a cor no dicionário `state_colors` em `draw()`.

### Adicionar um novo mapa (estado)

Em `src/core/brazil_maps.py`:
```python
STATES["Meu Estado"] = [
    (lon1, lat1), (lon2, lat2), ...  # polígono em graus decimais
]
STATE_ORDER.append("Meu Estado")
```

### Adicionar uma nova tela

Em `src/ui/menus.py`, crie a classe com os métodos `handle_event()`, `update()` e `draw()`.  
Em `main.py`, adicione o estado à máquina de estados.

### Adicionar uma nova skin

Em `src/config/game_config.py`, adicione ao final de `SKINS`:
```python
{"id": 10, "name": "Minha Skin",
 "primary": (R, G, B), "secondary": (R, G, B), "accent": (R, G, B)},
```

---

## 14. Referência de Configurações

### game_config.py — valores ajustáveis para balanceamento

```python
# Velocidade — aumente para jogo mais rápido
PLAYER_SPEED = 155.0
BOT_SPEED_BASE = 125.0

# IA — diminua os intervalos para bots mais reativos
AI_THINK_MIN = 0.08    # segundos (mínimo de reavaliação)
AI_THINK_MAX = 0.45    # segundos (máximo de reavaliação)
AI_HUNT_RANGE = 160.0  # px — alcance de detecção de trilha inimiga
AI_DANGER_RANGE = 90.0 # px — alcance de detecção de perigo

# Colisão — diminua KILL_RADIUS para colisão mais precisa
KILL_RADIUS = 11
SELF_IMMUNITY_POINTS = 22  # pontos imunes no fim da própria trilha

# Mundo — aumentar CELL_SIZE diminui a resolução mas melhora a performance
CELL_SIZE = 6
WORLD_COLS = 240
WORLD_ROWS = 240

# Power-ups (em powerups.py)
SPAWN_INTERVAL = 5.0   # segundos entre spawns
MAX_ITEMS = 6          # itens simultâneos no mapa
```

### sprite_config.py — campos disponíveis

| Campo | Tipo | Padrão | Descrição |
|---|---|---|---|
| `path` | str / None | None | Caminho do arquivo; None = fallback procedural |
| `scale` | float | 1.0 | Multiplicador de escala uniforme |
| `width` | int / None | None | Largura final em px (anula scale.x) |
| `height` | int / None | None | Altura final em px (anula scale.y) |
| `opacity` | int | 255 | Opacidade 0–255 |
| `frames` | int | 1 | Quadros de animação (spritesheet horizontal) |
| `fps` | float | 0 | Velocidade da animação |
| `loop` | bool | False | True = animação em loop |

---

*Documentação gerada para Paper.io 2 — Edição Brasil v2.0*  
*Assets Kenney.nl licenciados sob CC0 (Creative Commons Zero)*
