# CHANGELOG — TerritórIO: Edição Brasil

Histórico completo de versões, funcionalidades adicionadas, refatorações e correções de bugs.  
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

---

## [1.3.1] — Correção de Bug Crítico

### 🐛 Correções
- **`AttributeError: 'Bot' object has no attribute 'radius'`**
  - **Arquivo afetado:** `src/entities/player.py` — classe `Entity`
  - **Causa raiz:** `powerups.py` linha 229 acessa `bot.radius` ao verificar
    proximidade de coleta de power-up por bots. A constante `PLAYER_RADIUS`
    era usada diretamente nas funções internas de draw, mas nunca exposta como
    atributo de instância na classe `Entity` — base de `Bot` e `Player`.
  - **Correção aplicada:** adicionada propriedade `@property radius` na classe
    `Entity`, retornando `PLAYER_RADIUS`. Como `Bot` herda de `Entity`, o
    atributo passou a ser acessível em todas as subclasses.

  ```python
  # src/entities/player.py — Entity (ADICIONADO em v1.3.1)
  @property
  def radius(self) -> int:
      """Raio lógico da entidade para colisão e detecção de proximidade."""
      return PLAYER_RADIUS
  ```

  - **Impacto:** o jogo travava com `AttributeError` sempre que um bot
    se aproximava de um item coletável. Corrigido.
  - **Regressões:** nenhuma — `Player` e `Bot` herdam a propriedade;
    usos diretos de `PLAYER_RADIUS` em outros módulos não foram alterados.

### 🔀 Controle de Versão
- Resolvido conflito de merge (`CONFLICT add/add`) em `src/entities/player.py`
  durante `git pull --rebase origin main`.
- Estratégia adotada: `git checkout --ours` preservou o commit local com a
  correção, descartando a versão do remoto que não continha a propriedade.
- Rebase concluído com sucesso; branch `main` sincronizado com `origin/main`.

---

## [1.3.0] — Refatoração Acadêmica, Testes e Documentação

### ✨ Novas Funcionalidades
- **Nome original do jogo:** renomeado de *Paper.io 2 — Edição Brasil* para
  **TerritórIO — Edição Brasil** em todos os arquivos do projeto.
- **`src/config/difficulty.py`** — módulo novo com três perfis de dificuldade
  imutáveis (`@dataclass(frozen=True)`): `facil`, `medio`, `dificil`.
  - Diferença de dificuldade baseada em qualidade de decisão da IA, não em
    velocidade artificial.
  - 11 parâmetros configuráveis por perfil: `speed_multiplier`,
    `think_interval`, `hunt_range_factor`, `danger_range_factor`,
    `max_trail_factor`, `intercept_prob`, `hunt_prob`, `powerup_max_dist`,
    `lookahead_steps`, `priority_types`.
- **`src/core/log_setup.py`** — logging centralizado via módulo nativo
  `logging`. Ativado com `python main.py --debug`.
- **`assets/data/sprites.json`** — configuração externa de sprites em JSON.
  Permite adicionar, substituir e configurar sprites sem alterar código Python.
- **`tests/run_tests.py`** — runner de testes sem dependência de pytest.
  Executa via `python tests/run_tests.py` em qualquer ambiente.

### 🧪 Testes Automatizados
- **53 testes implementados, 53 passando, 0 falhas.**
- Suites cobertas:

  | Arquivo | Testes | O que cobre |
  |---|---|---|
  | `tests/test_world.py` | 11 | Inicialização, ownership, claim, líder |
  | `tests/test_trail.py` | 8 | Pontos, comprimento, is_near_start |
  | `tests/test_difficulty.py` | 10 | Perfis, ordenação lógica, get_profile |
  | `tests/test_collision.py` | 8 | Distância ponto-segmento, escudo, autocolisão |
  | `tests/test_sprite_manager.py` | 12 | Cache, fallback, escalonamento, listagem |
  | `tests/run_tests.py` | 53 | Todos os módulos (sem dependência de display) |

### 🤖 IA dos Bots — DifficultyProfile integrado
- `src/entities/bot.py` integrado ao `DifficultyProfile`: todos os parâmetros
  de IA (think_interval, probabilidades, lookahead) passam a ser controlados
  pelo perfil de dificuldade em vez de valores hardcoded.
- Distribuição de dificuldade por partida: 2 bots fáceis, 4 médios, 2 difíceis.
- Docstrings completas em todos os métodos públicos da classe `Bot`.

### 🖼️ Sistema de Sprites — JSON externo
- `src/systems/sprite_manager.py` reescrito para carregar configurações do
  arquivo JSON externo antes do fallback Python.
- Novo método `list_sprites(categoria)` para inspeção em runtime.
- Novo método `reload_config()` para hot-reload sem reiniciar o jogo.
- Docstrings completas com exemplos de uso em todos os métodos.

### 📝 Documentação
- `README.md` reescrito integralmente com contextualização acadêmica
  (CIn-UFPE / Sistemas de Informação / Introdução à Programação).
- `DOCUMENTACAO.md` atualizado com seções de testes, dificuldade e sprites.
- `ARCHITECTURE.md` atualizado com novos módulos e fluxo de execução.
- `CHANGELOG.md` criado (este arquivo).

### 🔧 Arquivos Modificados
| Arquivo | Tipo de alteração |
|---|---|
| `main.py` | Integração de `configure_logging`, suporte a `--debug` |
| `src/config/game_config.py` | Renomeação para TerritórIO, `SAVE_FILE` atualizado |
| `src/entities/bot.py` | Integração com `DifficultyProfile`, docstrings |
| `src/core/game.py` | Import de `DifficultyProfile`, distribuição de dificuldade |
| `src/systems/sprite_manager.py` | Carregamento via JSON, novos métodos, docstrings |
| `src/ui/menus.py` | Título atualizado para TerritórIO |
| `README.md` | Reescrito integralmente |
| `DOCUMENTACAO.md` | Atualizado |
| `ARCHITECTURE.md` | Atualizado |

### 🆕 Arquivos Criados
| Arquivo | Descrição |
|---|---|
| `src/config/difficulty.py` | Perfis de dificuldade configuráveis |
| `src/core/log_setup.py` | Logging centralizado |
| `assets/data/sprites.json` | Configuração externa de sprites |
| `tests/__init__.py` | Pacote Python para testes |
| `tests/run_tests.py` | Runner sem pytest |
| `tests/test_world.py` | Testes do sistema de território |
| `tests/test_trail.py` | Testes da trilha |
| `tests/test_difficulty.py` | Testes dos perfis de dificuldade |
| `tests/test_collision.py` | Testes de colisão (requer pytest) |
| `tests/test_sprite_manager.py` | Testes do gerenciador de sprites (requer pytest) |
| `CHANGELOG.md` | Este arquivo |

---

## [1.2.0] — 60 FPS, Encerramento Correto e Script Ubuntu

### ✨ Novas Funcionalidades
- **Travamento real de 60 FPS** via `clock.tick_busy_loop(FPS)`.
  - `tick_busy_loop` usa busy-wait com precisão sub-milissegundo, superior
    ao `tick()` em sistemas com resolução de scheduler de 15 ms (Windows).
  - Delta time limitado a `MAX_DT = TARGET_DT * 3` para evitar saltos
    de posição após alt-tab ou pausa do SO.
- **Encerramento correto pelo X da janela:**
  - `pygame.QUIT` chama `_quit()` que executa `pygame.mixer.quit()` →
    `pygame.quit()` → `sys.exit(0)`.
  - Alt+F4 tratado explicitamente via `pygame.K_F4 + KMOD_ALT`.
  - Save automático antes de encerrar em qualquer caminho de saída.
- **`iniciar.sh`** — script Bash para Ubuntu/Linux:
  - Detecta Python 3.9+ entre múltiplos executáveis disponíveis.
  - Instala `python3-venv` via apt se ausente.
  - Instala dependências SDL2 (`libsdl2-dev`, `libsdl2-mixer-dev`, etc.)
    se ausentes.
  - Cria ambiente virtual isolado em `.venv/`.
  - Instala `pygame>=2.5.0` e `numpy>=1.24.0` no venv.
  - Verifica imports antes de iniciar o jogo.
  - Usa `exec` para substituir o processo shell pelo Python.
- **FPS exibido no título da janela** — atualizado a cada 1 segundo para
  não sobrecarregar chamadas de `set_caption`.

### 🔧 Arquivos Modificados
| Arquivo | Alteração |
|---|---|
| `main.py` | `tick_busy_loop`, `_quit()`, Alt+F4, FPS no título |

### 🆕 Arquivos Criados
| Arquivo | Descrição |
|---|---|
| `iniciar.sh` | Script de instalação e inicialização para Ubuntu |

---

## [1.1.0] — IA Avançada, Power-ups para Bots e Modo Predador

### ✨ Novas Funcionalidades

#### IA dos Bots — FSM de 6 estados
- Sistema anterior (4 estados simples) substituído por **FSM com avaliação
  de utilidade em 6 estados**:

  | Estado | Prioridade | Comportamento |
  |---|---|---|
  | `evade` | 1ª | Fuga quando trilha está ameaçada |
  | `return` | 2ª | Retorno ao território com trilha longa |
  | `collect_pu` | 3ª | Coleta oportunista de power-ups |
  | `intercept` | 4ª | Interceptação preditiva (N passos à frente) |
  | `hunt` | 5ª | Corte direto da trilha inimiga |
  | `expand` | 6ª | Captura estratégica de território |

- **Anti-stuck automático:** força guinada perpendicular se o bot não se
  mover mais de 2 px em 1,5 s.
- **Indicador visual de estado:** ponto colorido acima de cada bot mostra
  o estado atual em tempo real.
- **Cor de trilha por estado:** trilha ligeiramente modificada durante
  `hunt` (avermelhada), `intercept` (alaranjada) e `evade` (amarelada).

#### Bots coletam power-ups
- Função de utilidade avalia cada item disponível: `score = proximidade +
  bônus_tipo - penalidade_trilha`.
- Cada estado da FSM tem lista de prioridade de tipos de power-up.
- Bomba de tinta funciona para bots: conquista área real no grid do `World`.
- Efeitos temporários (TURBO) expiram corretamente nos bots via
  `update_bot_effects()`.

#### Sprites dos power-ups
- 5 ícones PNG 48×48 gerados por código Python puro (sem dependências
  externas): `size_up.png`, `speed.png`, `bomb.png`, `shield.png`,
  `eagle.png`.
- Sprites registrados em `sprite_config.py` com dimensões 32×32.

#### Modo Predador aprimorado
- Badge com glow exterior pulsante em 4 camadas animadas.
- Radar tático com linha de varredura giratória.
- Power-ups visíveis no minimapa com cores características.
- Bots exibem estado atual no radar (borda colorida).
- Painel lateral com kills, % de território e lista de bots vivos.

### 🔧 Arquivos Modificados
| Arquivo | Alteração |
|---|---|
| `src/entities/bot.py` | FSM de 6 estados, anti-stuck, utilidade de power-up |
| `src/systems/powerups.py` | Suporte a coleta por bots, `_apply_to_bot`, `update_bot_effects` |
| `src/core/game.py` | `_bot_bomb_claim`, passagem de itens à IA dos bots |
| `src/ui/hud.py` | Radar tático, painel de estatísticas Predador |

### 🆕 Arquivos Criados
| Arquivo | Descrição |
|---|---|
| `assets/sprites/powerups/size_up.png` | Ícone Expansão |
| `assets/sprites/powerups/speed.png` | Ícone Turbo |
| `assets/sprites/powerups/bomb.png` | Ícone Bomba |
| `assets/sprites/powerups/shield.png` | Ícone Escudo |
| `assets/sprites/powerups/eagle.png` | Ícone Visão de Águia |

---

## [1.0.0] — Arquitetura Modular Completa

### ✨ Funcionalidades Implementadas

#### Estrutura e Arquitetura
- Projeto reorganizado em arquitetura modular com responsabilidades separadas:
  `src/config/`, `src/core/`, `src/entities/`, `src/systems/`, `src/ui/`.
- Instância global `sprite_manager` disponível para qualquer módulo via
  `from src.systems.sprite_manager import sprite_manager`.
- `DifficultyProfile` como `@dataclass(frozen=True)` — imutável e seguro
  para uso em múltiplas instâncias simultâneas.

#### Jogo
- 10 skins de personagem selecionáveis.
- 8 bots adversários por partida.
- 5 power-ups coletáveis com ícones e efeitos completos:
  - **EXPANSÃO** (4 s): dobra raio e espessura da trilha.
  - **TURBO** (3 s): dobra velocidade de movimento.
  - **BOMBA** (instantâneo): conquista área circular de 90 px.
  - **ESCUDO** (3 s): imunidade a eliminações externas.
  - **VISÃO DE ÁGUIA** (5 s): zoom out mostrando ~50% do mapa.
- Buff passivo de borda: velocidade ×1,5 ao tocar bordas (linger 1,5 s).
- Autocolisão do jogador removida por design — a própria trilha não elimina.
- 27 mapas dos estados brasileiros com polígonos geográficos reais.
- Progressão por nível: 1 estado por nível, em sequência.
- Modo Predador ao atingir 4+ eliminações.
- Câmera suave com interpolação (`lerp`) e zoom Eagle Eye.
- Sistema de partículas para coleta, captura e eliminação.
- Salvamento automático de progresso em `territorio_save.json`.

#### Interface
- Menu principal com partículas animadas e grade decorativa.
- Tela de seleção de skin com 10 opções e preview animado.
- HUD com barra superior, ranking lateral em tempo real e alerta de
  vulnerabilidade.
- Painel de efeitos ativos com barra de progresso e timer.
- Badge Predador animada com glow multicamadas.
- Minimapa tático exclusivo do Predador.
- Tela de game over com estatísticas e confetti na vitória.
- Progressão de nível com botão "Próximo Nível".

#### Técnico
- Loop principal a 60 FPS com `tick_busy_loop`.
- `pygame.QUIT` → `sys.exit(0)` (encerramento completo pelo X).
- Sistema de sprites com cache, fallback e carregamento via JSON externo.
- Logging configurável (`--debug`) via módulo nativo `logging`.
- Script `iniciar.sh` para Ubuntu com criação automática de venv.

---

## Versões Resumidas

| Versão | Data (aprox.) | Destaques |
|---|---|---|
| **1.3.1** | Novembro/2025 | Bugfix crítico: `Bot.radius` via `Entity.@property`; merge conflict resolvido |
| **1.3.0** | Novembro/2025 | Nome TerritórIO; `DifficultyProfile`; logging; JSON de sprites; 53 testes |
| **1.2.0** | Novembro/2025 | 60 FPS real; encerramento pelo X; `iniciar.sh` para Ubuntu |
| **1.1.0** | Novembro/2025 | IA de 6 estados; bots coletam power-ups; Predador aprimorado; sprites PNG |
| **1.0.0** | Novembro/2025 | Arquitetura modular completa; 27 mapas; 5 power-ups; HUD; menus |

---

## Bugs Conhecidos / Pendências

| ID | Descrição | Prioridade | Status |
|---|---|---|---|
| — | Sprites PNG dos power-ups gerados por código Python puro têm qualidade limitada; substituição por assets profissionais melhora a apresentação visual | Baixa | Aberto |
| — | Polígonos dos estados brasileiros são simplificados (não são os dados oficiais do IBGE com alta resolução) | Baixa | Aberto |
| — | `test_collision.py` e `test_sprite_manager.py` requerem `pytest` instalado; os demais funcionam sem dependências externas | Baixa | Aberto |

---

## Padrão de Versionamento

O projeto segue [Semantic Versioning](https://semver.org/lang/pt-BR/):

```
MAJOR.MINOR.PATCH
  │     │     └── Correção de bug (sem mudança de API)
  │     └──────── Nova funcionalidade (retrocompatível)
  └────────────── Mudança incompatível de API ou arquitetura
```
