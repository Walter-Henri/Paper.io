# TerritórIO — Edição Brasil 🇧🇷

> **Conquiste. Expanda. Domine.**
> Um jogo arcade de captura de território inspirado em Paper.io, desenvolvido em Python com Pygame.

---

## Contextualização Acadêmica

| | |
|---|---|
| **Disciplina** | Introdução à Programação (I.P.) |
| **Curso** | Bacharelado em Sistemas de Informação (S.I.) |
| **Instituição** | Centro de Informática — Universidade Federal de Pernambuco (CIn-UFPE) |
| **Tipo** | Projeto em equipe para avaliação semestral |

### Equipe de Desenvolvimento

| Nome | Função |
|---|---|
| _(preencher)_ | _(preencher)_ |
| _(preencher)_ | _(preencher)_ |
| _(preencher)_ | _(preencher)_ |

> **Nota:** Os campos acima devem ser preenchidos pelos integrantes da equipe antes da entrega final.

### Objetivos Acadêmicos

- Praticar organização de código em módulos com responsabilidades bem definidas
- Implementar lógica de jogo em tempo real com controle de FPS
- Desenvolver inteligência artificial com máquina de estados finitos (FSM)
- Trabalhar com sistemas gráficos via Pygame (superfícies, animações, câmera)
- Produzir documentação técnica de qualidade profissional
- Exercitar trabalho colaborativo em equipe de desenvolvimento

---

## Descrição do Jogo

**TerritórIO** é um jogo arcade competitivo de conquista de território. O jogador controla um personagem que traça trilhas ao se mover pelo mapa. Ao fechar um loop retornando ao próprio território, toda a área interior é conquistada. Quanto maior o território, melhor a pontuação.

O diferencial da **Edição Brasil** é a progressão por **27 mapas únicos**, cada um com a forma geográfica real de um estado brasileiro. O jogo inclui 8 bots adversários com IA adaptativa em três níveis de dificuldade, 5 tipos de power-ups coletáveis com ícones próprios, e um sistema de sprites completamente modular e configurável via arquivo JSON.

### Mecânicas Principais

| Mecânica | Descrição |
|---|---|
| **Captura de território** | Mova-se fora do seu território → trilha é desenhada → feche o loop → área interior é conquistada |
| **Eliminação** | Atravesse a trilha de um inimigo enquanto ele está vulnerável fora do seu território |
| **Vulnerabilidade** | Enquanto sua trilha está aberta, um inimigo pode cortá-la e eliminar você |
| **Buff de borda** | Velocidade ×1,5 ao tocar a borda do mapa (persiste 1,5 s após sair) |
| **Modo Predador** | Ao eliminar ≥ 4 adversários, desbloqueia radar tático e painel de estatísticas |

---

## Funcionalidades Implementadas

### Jogo
- [x] 10 skins de personagem selecionáveis com cores únicas
- [x] 8 bots adversários por partida com IA de 6 estados
- [x] 3 perfis de dificuldade: Fácil, Médio e Difícil (misturados por partida)
- [x] 5 power-ups coletáveis com ícones PNG próprios
- [x] Bots coletam power-ups estrategicamente
- [x] 27 mapas dos estados brasileiros com polígonos geográficos reais
- [x] Progressão por nível (1 estado por nível, em sequência)
- [x] Modo Predador com radar tático e painel de estatísticas
- [x] Câmera suave com interpolação e zoom Eagle Eye
- [x] Sistema de partículas para efeitos visuais

### Técnico
- [x] Arquitetura modular com responsabilidades separadas
- [x] Sistema de sprites configurável via `assets/data/sprites.json`
- [x] Carregamento com cache e fallback seguro (nunca trava o jogo)
- [x] Travamento de 60 FPS com `tick_busy_loop`
- [x] Fechamento correto pelo X da janela (`pygame.QUIT → sys.exit`)
- [x] Logging configurável via `--debug` (módulo nativo `logging`)
- [x] Salvamento automático de progresso (JSON)
- [x] Script de instalação e inicialização para Ubuntu (`iniciar.sh`)
- [x] Suite de testes automatizados (35 testes, 0 falhas)

---

## Requisitos e Instalação

### Pré-requisitos

| Requisito | Versão mínima |
|---|---|
| Python | 3.9+ |
| pygame | 2.5.0+ |
| numpy | 1.24.0+ |

### Instalação rápida (Ubuntu/Linux)

```bash
# Clone ou extraia o projeto
cd territorIO

# Dê permissão ao script e execute
chmod +x iniciar.sh
./iniciar.sh
```

O script `iniciar.sh` executa automaticamente:
1. Verifica Python 3.9+
2. Instala `python3-venv` via apt (se necessário)
3. Instala SDL2 e dependências de sistema (se necessário)
4. Cria ambiente virtual isolado em `.venv/`
5. Instala `pygame` e `numpy` no venv
6. Verifica os imports e inicia o jogo

### Instalação manual

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pygame>=2.5.0 numpy>=1.24.0
python main.py
```

### Modo debug (verbose)

```bash
python main.py --debug
```

---

## Controles

| Ação | Tecla |
|---|---|
| Mover para cima | ↑ ou W |
| Mover para baixo | ↓ ou S |
| Mover para a esquerda | ← ou A |
| Mover para a direita | → ou D |
| Pausar / continuar | P |
| Mute / desmute áudio | M |
| Voltar ao menu | ESC |
| Fechar o jogo | X da janela / Alt+F4 |

---

## Estrutura de Diretórios

```
territorIO/
│
├── main.py                        ← Ponto de entrada; loop principal; máquina de estados
├── iniciar.sh                     ← Script de instalação e inicialização (Ubuntu)
├── requirements.txt               ← Dependências Python
├── territorio_save.json           ← Criado automaticamente ao jogar
│
├── README.md                      ← Este arquivo
├── ARCHITECTURE.md                ← Documentação de arquitetura técnica
├── DOCUMENTACAO.md                ← Documentação técnica completa em português
│
├── assets/
│   ├── data/
│   │   └── sprites.json           ← Configuração externa de todos os sprites ⭐
│   ├── fonts/
│   │   ├── Kenney Future.ttf
│   │   └── Kenney Future Narrow.ttf
│   ├── audio/
│   │   └── *.ogg                  ← SFX Kenney (CC0)
│   ├── animations/                ← Futuras sequências de animação
│   └── sprites/
│       ├── players/               ← Sprites do jogador (PNG opcional)
│       ├── bots/                  ← Sprites dos bots (PNG opcional)
│       ├── powerups/              ← 5 ícones PNG gerados automaticamente ⭐
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
    ├── test_world.py              ← 11 testes para World
    ├── test_trail.py              ←  8 testes para Trail
    ├── test_difficulty.py         ← 10 testes para DifficultyProfile
    ├── test_collision.py          ←  8 testes para collision (com pytest)
    └── test_sprite_manager.py     ← 12 testes para SpriteManager (com pytest)
```

---

## Tecnologias e Bibliotecas

### Pygame (biblioteca central — obrigatória)

**Versão:** ≥ 2.5.0  
**Finalidade:** Motor gráfico e de jogo completo.

Pygame é a espinha dorsal do projeto. **Nenhuma outra biblioteca substitui suas funções centrais.** É responsável por:

| Função do Pygame | Uso no TerritórIO |
|---|---|
| `pygame.display` | Criação e gerenciamento da janela 1280×720 |
| `pygame.event` | Captura de teclado, mouse e evento QUIT |
| `pygame.Surface` | Renderização de território, trilhas, personagens e efeitos |
| `pygame.draw` | Círculos, linhas, retângulos para todos os elementos visuais procedurais |
| `pygame.transform` | Escalonamento suave de sprites (`smoothscale`) |
| `pygame.image` | Carregamento de PNG para sprites e ícones |
| `pygame.font` | Renderização de textos na HUD, menus e badges |
| `pygame.time.Clock` | Travamento em 60 FPS via `tick_busy_loop` |
| `pygame.mixer` | Reprodução de efeitos sonoros (.ogg) |
| `pygame.SRCALPHA` | Transparência em partículas, halos e overlays |

### NumPy (biblioteca auxiliar)

**Versão:** ≥ 1.24.0  
**Localização:** `src/systems/audio.py`  
**Justificativa técnica:** Geração de formas de onda de áudio (sine, square, sawtooth) para SFX procedurais do jogo.

**Por que não Pygame sozinho?** `pygame.mixer` reproduz arquivos de áudio, mas não oferece API para *sintetizar* waveforms em memória. Para gerar SFX procedurais (sons de captura, eliminação, vitória) sem depender de arquivos externos adicionais, é necessário criar arrays de amostras de áudio diretamente — tarefa para a qual NumPy é a ferramenta padrão da indústria.

```python
# Uso real em src/systems/audio.py
import numpy as np

def _tone(freq, duration, volume=0.3, sample_rate=22050, wave="sine"):
    n    = int(sample_rate * duration)
    t    = np.linspace(0, duration, n, False)          # vetor de tempo
    data = np.sin(2 * np.pi * freq * t)               # waveform senoidal
    data = data * (np.linspace(1.0, 0.0, n) ** 1.4)   # decay exponencial
    audio = (data * volume * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack((audio, audio)))
```

**Funções utilizadas:**

| Função NumPy | Responsabilidade |
|---|---|
| `np.linspace(start, stop, n)` | Cria vetor uniforme de N amostras de tempo |
| `np.sin(array)` | Aplica função seno elemento-a-elemento (onda senoidal) |
| `np.sign(array)` | Gera onda quadrada via sinal do seno |
| `np.floor(array)` | Gera onda dente-de-serra |
| `array.astype(np.int16)` | Converte float64 para formato PCM de 16 bits do pygame |
| `np.column_stack((L, R))` | Intercala canais esquerdo/direito para áudio estéreo |

### Módulos da Biblioteca Padrão do Python

Estes módulos fazem parte do Python e **não requerem instalação adicional**:

| Módulo | Uso no projeto |
|---|---|
| `json` | Leitura de `sprites.json` e do arquivo de save |
| `logging` | Registro de eventos, erros e debug configurável |
| `pathlib.Path` | Manipulação de caminhos de arquivo multiplataforma |
| `math` | Funções trigonométricas (IA, câmera, partículas) |
| `random` | Aleatoriedade controlada (spawn, IA, power-ups) |
| `sys` | Encerramento seguro via `sys.exit()` |
| `os` | Verificação de existência de arquivos |
| `dataclasses` | `DifficultyProfile` imutável com `@dataclass(frozen=True)` |

---

## Sistema de Sprites

### Como funciona

```
assets/data/sprites.json        ← define chave + caminho + parâmetros
         ↓ leitura na primeira chamada
SpriteManager.get("chave")      ← carrega, processa e armazena em cache
         ↓ Surface pronta
player.py / bot.py / powerups.py ← recebem e renderizam o sprite
```

Se o arquivo PNG não existir, o `SpriteManager` retorna um **Surface de fallback** (círculo cinza 28×28 px) sem travar o jogo.

### Como adicionar um sprite novo

**Passo 1** — Coloque o arquivo PNG na pasta correta:
```
assets/sprites/players/meu_personagem.png
```

**Passo 2** — Registre em `assets/data/sprites.json`:
```json
"player.skin_nova": {
    "descricao": "Descrição do sprite",
    "path":    "assets/sprites/players/meu_personagem.png",
    "scale":   1.0,
    "width":   null,
    "height":  null,
    "opacity": 255,
    "frames":  1,
    "fps":     0,
    "loop":    false,
    "categoria": "player"
}
```

**Passo 3** — Use em qualquer lugar do código:
```python
from src.systems.sprite_manager import sprite_manager
sprite = sprite_manager.get("player.skin_nova")
surface.blit(sprite, (x, y))
```

**Nenhum outro arquivo Python precisa ser modificado.**

### Como substituir um sprite existente

Edite apenas o campo `"path"` no `sprites.json`. Na próxima inicialização do jogo, o novo arquivo será carregado automaticamente.

Para forçar recarga sem reiniciar:
```python
sprite_manager.reload_config()
```

### Como configurar dimensões

```json
"meu.sprite": {
    "path":    "assets/sprites/players/sprite.png",
    "scale":   1.5,    ← multiplica as dimensões originais por 1.5
    "width":   48,     ← força largura (anula scale.x)
    "height":  48,     ← força altura (anula scale.y)
    "opacity": 200     ← 0=transparente, 255=opaco
}
```

---

## Inteligência Artificial dos Bots

Os bots usam uma **Máquina de Estados Finitos (FSM)** com **avaliação de utilidade** em 6 estados. A cada intervalo de reavaliação (configurado pelo perfil de dificuldade), o bot avalia qual estado maximiza seu benefício estratégico.

### Os 6 estados da FSM

| Estado | Prioridade | Trigger | Comportamento |
|---|---|---|---|
| `evade` | 1ª | Inimigo próximo da trilha | Foge para o próprio território |
| `return` | 2ª | Trilha muito longa | Volta pelo caminho mais curto |
| `collect_pu` | 3ª | Power-up lucrativo próximo | Desvia para coletar o item |
| `intercept` | 4ª | Inimigo com trilha exposta | Prevê posição futura e corta o caminho |
| `hunt` | 5ª | Trilha inimiga acessível | Mira o ponto médio da trilha (mais vulnerável) |
| `expand` | 6ª | Padrão | Captura território de forma estratégica |

### Coleta de power-ups pelos bots

A função de utilidade avalia cada item disponível:

```
score = (1 - distância/dist_max) + bônus_tipo - penalidade_trilha
```

Onde:
- **bônus_tipo**: cada estado tem uma lista de tipos preferidos (ex.: estado `evade` prefere ESCUDO)
- **penalidade_trilha**: desconta quando a trilha está muito exposta (risco alto)
- O bot só desvia se `score > 0.20` (limiar de lucro mínimo)

### Interceptação preditiva

O estado `intercept` prevê onde o inimigo estará em N passos à frente:

```python
pred_x = e.x + e.direction[0] * e.speed * think_interval * lookahead_steps
pred_y = e.y + e.direction[1] * e.speed * think_interval * lookahead_steps
```

Bots difíceis têm `lookahead_steps = 4` (preveem 4 ciclos à frente); bots fáceis preveem apenas 1.

### Três níveis de dificuldade

A diferença entre níveis está na **qualidade das decisões**, não na velocidade:

| Parâmetro | Fácil | Médio | Difícil |
|---|---|---|---|
| Velocidade | ×0,82 | ×0,95 | ×1,08 |
| Reavaliação de IA | 0,55 s | 0,32 s | 0,14 s |
| Prob. de interceptar | 8% | 22% | 40% |
| Prob. de caçar | 12% | 28% | 45% |
| Distância p/ power-up | 110 px | 180 px | 260 px |
| Passos de previsão | 1 | 2 | 4 |

### Anti-stuck

Se o bot permanecer imóvel por mais de 1,5 s, o mecanismo anti-stuck é ativado:
1. Tenta virar 90° para a esquerda ou direita
2. Fallback: direção aleatória não reversa

---

## Power-ups

| Ícone | Nome | Duração | Efeito |
|---|---|---|---|
| 🟠 | **EXPANSÃO** | 4 s | Dobra raio e espessura da trilha |
| 🔵 | **TURBO** | 3 s | Dobra velocidade de movimento |
| 🔴 | **BOMBA** | Instantâneo | Conquista área circular de 90 px ao redor |
| 🟢 | **ESCUDO** | 3 s | Imunidade a eliminações externas |
| 🟣 | **VISÃO** | 5 s | Zoom out mostrando ~50% do mapa |

**Regras especiais:**
- Re-coleta **reinicia** o timer — não acumula duração
- Bots coletam power-ups estrategicamente baseados no estado atual
- **Buff de borda passivo:** velocidade ×1,5 ao tocar bordas (linger 1,5 s)
- Combinação Turbo + Borda: ×2,0 × ×1,5 = **×3,0 de velocidade**

---

## Mapas dos Estados Brasileiros

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

---

## Testes

```bash
# Com pytest instalado:
python -m pytest tests/ -v

# Sem pytest (todos os ambientes):
python tests/run_tests.py
```

### Resultado dos testes (última execução)

| Suite | Testes | Resultado |
|---|---|---|
| `test_world.py` | 11 | ✅ Todos passando |
| `test_trail.py` | 8 | ✅ Todos passando |
| `test_difficulty.py` | 10 | ✅ Todos passando |
| `test_collision.py` | 8 | ✅ Todos passando (requer pytest) |
| `test_sprite_manager.py` | 12 | ✅ Todos passando (requer pytest) |
| **collision._point_to_segment_dist** | 4 | ✅ Todos passando |
| **brazil_maps** | 6 | ✅ Todos passando |
| **game_config** | 7 | ✅ Todos passando |
| **sprites.json** | 4 | ✅ Todos passando |
| **Total** | **70** | ✅ **0 falhas** |

---

## Créditos e Referências

### Assets visuais e sonoros
- **Kenney UI Pack** — botões, ícones e fontes (CC0, domínio público)  
  [kenney.nl](https://kenney.nl)

### Referências técnicas
- [Documentação oficial do Pygame](https://www.pygame.org/docs/)
- [Documentação do NumPy](https://numpy.org/doc/)
- [PEP 8 — Guia de Estilo Python](https://peps.python.org/pep-0008/)
- [Finite State Machines in Games](https://gameprogrammingpatterns.com/state.html)
- [Paper.io 2 (inspiração de mecânicas)](https://paper-io.com)

### Dados geográficos
- Polígonos dos estados brasileiros simplificados em coordenadas decimais (lon, lat)
- Baseados em dados de domínio público do IBGE

---

## Licença

Este projeto foi desenvolvido para fins acadêmicos no contexto da disciplina de Introdução à Programação do CIn-UFPE.

Assets de terceiros (Kenney) estão licenciados sob **CC0 (Creative Commons Zero)** — domínio público.

---

*TerritórIO — Edição Brasil | CIn-UFPE | Introdução à Programação*
