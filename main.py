
from __future__ import annotations
import sys
import os
import json
import pygame

# Garante que src/ seja encontrado independente do diretório de execução
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configura logging antes de qualquer import do projeto
from src.core.log_setup import configure_logging
configure_logging(debug="--debug" in sys.argv)

from src.config.game_config  import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WINDOW_TITLE, SKINS, SAVE_FILE,
)
from src.systems.assets         import Assets
from src.systems.audio          import AudioManager
from src.systems.sprite_manager import sprite_manager
from src.core.game              import GameSession
from src.ui.hud                 import HUD
from src.ui.menus               import MainMenu, SkinSelect, GameOverScreen


# Estados
STATE_MENU     = "menu"
STATE_SELECT   = "select"
STATE_PLAYING  = "playing"
STATE_GAMEOVER = "gameover"

TARGET_DT = 1.0 / FPS       # 1/60 s — passo fixo da simulação
MAX_DT    = TARGET_DT * 5   # acumula no máximo ~5 frames de lag


# Persistência
def _load_save() -> dict:
    try:
        if os.path.isfile(SAVE_FILE):
            with open(SAVE_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _write_save(data: dict) -> None:
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


# Encerramento seguro
def _quit() -> None:
    """Encerra pygame e o processo completamente (garante saída pelo X da janela)."""
    pygame.mixer.quit()
    pygame.quit()
    sys.exit(0)


# Loop principal
def main() -> None:
    pygame.init()

    # Mixer separado do init principal para evitar delay de áudio
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    except Exception:
        pass

    # Janela com DOUBLEBUF + HWSURFACE para melhor performance de flip
    flags  = pygame.DOUBLEBUF | pygame.HWSURFACE
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
    pygame.display.set_caption(WINDOW_TITLE)

    # Clock com travamento real em FPS: tick_busy_loop é mais preciso que tick()
    # em sistemas onde o scheduler tem resolução de 15ms
    clock = pygame.time.Clock()

    # Sistemas compartilhados
    assets = Assets()
    audio  = AudioManager()

    # Pré-carrega sprites usados com frequência — evita hitches em runtime
    sprite_manager.preload([
        "player.default", "bot.default",
        "powerup.size_up", "powerup.speed",
        "powerup.bomb",    "powerup.shield", "powerup.eagle",
    ])

    # Telas de UI (criadas uma única vez, reutilizadas)
    main_menu    = MainMenu(assets)
    skin_select  = SkinSelect(assets)
    gameover_scr = GameOverScreen(assets)
    hud          = HUD(assets)

    # Estado persistido
    save_data  = _load_save()
    high_score = float(save_data.get("high_score", 0))
    level      = int(save_data.get("level", 1))
    skin_idx   = int(save_data.get("skin_id", 0))
    skin_select.selected = skin_idx if 0 <= skin_idx < len(SKINS) else 0

    # Máquina de estados
    state:   str                = STATE_MENU
    session: GameSession | None = None
    paused                      = False

    # FPS display — atualiza o título a cada 1 segundo
    _fps_timer  = 0.0
    _fps_display = 0
    # Acumulador de timestep fixo: a lógica roda sempre a 60 Hz,
    # independentemente de flutuações do display.
    _sim_acc = 0.0

    running = True
    while running:

        # Trava em 60 FPS
        # tick limita o render; a simulação usa passo fixo TARGET_DT.
        frame_dt = clock.tick(FPS) / 1000.0
        _sim_acc += min(frame_dt, MAX_DT)

        # Eventos
        for event in pygame.event.get():

            # X da janela, Alt+F4, Ctrl+W, sinal de fechamento do SO
            if event.type == pygame.QUIT:
                _write_save({
                    "high_score": high_score,
                    "skin_id":    skin_select.selected,
                    "level":      level,
                })
                _quit()          # encerra imediatamente — não sai do loop

            # Mute global (qualquer estado)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    audio.toggle()
                # Alt+F4 manual via teclado (algumas distros não geram QUIT)
                if event.key == pygame.K_F4 and (
                        pygame.key.get_mods() & pygame.KMOD_ALT):
                    _write_save({
                        "high_score": high_score,
                        "skin_id":    skin_select.selected,
                        "level":      level,
                    })
                    _quit()

            # Menu principal
            if state == STATE_MENU:
                action = main_menu.handle_event(event)
                if action == "play":
                    audio.play("click")
                    state = STATE_SELECT
                elif action == "quit":
                    _write_save({
                        "high_score": high_score,
                        "skin_id":    skin_select.selected,
                        "level":      level,
                    })
                    _quit()

            # Seleção de skin
            elif state == STATE_SELECT:
                action = skin_select.handle_event(event)
                if action == "confirm":
                    audio.play("click")
                    session = GameSession(skin_select.get_skin(), level)
                    paused  = False
                    state   = STATE_PLAYING
                    audio.play("start")
                elif action == "back":
                    audio.play("click")
                    state = STATE_MENU

            # Partida
            elif state == STATE_PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        paused = not paused
                    elif event.key == pygame.K_ESCAPE:
                        state = STATE_MENU

            # Game Over / Vitória
            elif state == STATE_GAMEOVER:
                action = gameover_scr.handle_event(event)
                if action == "restart":
                    audio.play("click")
                    state = STATE_SELECT
                elif action == "menu":
                    audio.play("click")
                    state = STATE_MENU
                elif action == "next_level":
                    audio.play("click")
                    session = GameSession(skin_select.get_skin(), level)
                    paused  = False
                    state   = STATE_PLAYING
                    audio.play("start")

        # Update com passo fixo de 1/60 s
        while _sim_acc >= TARGET_DT:
            _sim_acc -= TARGET_DT
            dt = TARGET_DT

            if state == STATE_MENU:
                main_menu.update(dt)

            elif state == STATE_PLAYING and session:
                if not paused:
                    keys = pygame.key.get_pressed()
                    session.update(dt, keys)

                    if session.finished:
                        score = session.player.score_percent
                        if score > high_score:
                            high_score = score
                        if session.won:
                            audio.play("victory")
                            level += 1
                        else:
                            audio.play("death")
                        gameover_scr.set_stats(
                            score,
                            session.player.kills,
                            won=session.won,
                            level=level,
                            state_name=session.state_name,
                        )
                        _write_save({
                            "high_score": high_score,
                            "skin_id":    skin_select.selected,
                            "level":      level,
                        })
                        state = STATE_GAMEOVER
                        break

        # Renderização (uma vez por frame, após a simulação)
        screen.fill((18, 20, 28))

        if state == STATE_MENU:
            main_menu.draw(screen)

        elif state == STATE_SELECT:
            skin_select.draw(screen)

        elif state == STATE_PLAYING and session:
            session.draw(screen, assets, paused)
            hud.draw(screen, session, paused)

        elif state == STATE_GAMEOVER:
            gameover_scr.draw(screen)

        # Flip — envia o frame renderizado para o display
        pygame.display.flip()

        # Título com FPS (atualiza a cada 1 s para não sobrecarregar)
        _fps_timer += frame_dt
        if _fps_timer >= 1.0:
            _fps_timer   = 0.0
            _fps_display = int(round(clock.get_fps()))
            pygame.display.set_caption(
                f"{WINDOW_TITLE}  |  Nível {level}"
                f"  |  {_fps_display} FPS"
            )


if __name__ == "__main__":
    main()
