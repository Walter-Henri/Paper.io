"""
sprite_manager.py — TerritórIO: Edição Brasil
----------------------------------------------
Responsabilidade:
    Carregamento, cache e disponibilização centralizada de todos os sprites.
    Lê configurações do arquivo JSON externo (assets/data/sprites.json).
    Aplica escala, opacidade e redimensionamento.
    Retorna fallback seguro quando um arquivo não existe — nunca encerra o jogo.
    Suporta animações por spritesheet horizontal.

Não contém lógica de jogo, colisão ou comportamento de entidades.

Uso básico:
    from src.systems.sprite_manager import sprite_manager
    surf = sprite_manager.get("powerup.speed")          # 32x32 PNG
    surf = sprite_manager.get_scaled("player.default", 24, 24)
    anim = sprite_manager.get_animation("player.run")   # AnimationState
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import pygame

logger = logging.getLogger(__name__)

# Raiz do projeto (três níveis acima de src/systems/)
_ROOT = Path(__file__).resolve().parent.parent.parent

# Arquivo de configuração externo
_JSON_CONFIG = _ROOT / "assets" / "data" / "sprites.json"

# Fallback interno (usado quando JSON não carrega)
from src.config.sprite_config import SPRITE_CONFIG as _FALLBACK_CONFIG


#
# AnimationState
#
class AnimationState:
    """
    Controla a reprodução de uma animação com múltiplos quadros.

    Parâmetros:
        frames  — lista de pygame.Surface (cada quadro)
        fps     — velocidade em quadros/segundo (0 = estático)
        loop    — True para reprodução em loop contínuo

    Atributos públicos:
        current   — Surface do quadro atual
        finished  — True quando animação one-shot chegou ao fim
    """

    def __init__(self, frames: List[pygame.Surface],
                 fps: float, loop: bool) -> None:
        self.frames   = frames
        self.fps      = fps
        self.loop     = loop
        self._elapsed = 0.0
        self._index   = 0
        self.finished = False

    #
    def update(self, dt: float) -> None:
        """
        Avança a animação.

        Parâmetros:
            dt — delta time em segundos desde o último frame
        """
        if self.finished or self.fps <= 0 or len(self.frames) <= 1:
            return
        self._elapsed += dt
        frame_dur = 1.0 / self.fps
        while self._elapsed >= frame_dur:
            self._elapsed -= frame_dur
            self._index   += 1
            if self._index >= len(self.frames):
                if self.loop:
                    self._index = 0
                else:
                    self._index   = len(self.frames) - 1
                    self.finished = True
                    break

    def reset(self) -> None:
        """Reinicia a animação do primeiro quadro."""
        self._elapsed = 0.0
        self._index   = 0
        self.finished = False

    @property
    def current(self) -> pygame.Surface:
        """Surface do quadro corrente."""
        return self.frames[self._index]


#
# SpriteManager
#
class SpriteManager:
    """
    Gerenciador centralizado de sprites.

    Carrega configurações do JSON externo (assets/data/sprites.json).
    Mantém cache interno para evitar recarregamentos.
    Retorna Surface de fallback para chaves não encontradas ou arquivos ausentes.

    Como adicionar um sprite novo:
        1. Coloque o arquivo PNG em assets/sprites/<categoria>/
        2. Adicione uma entrada em assets/data/sprites.json
        3. Use sprite_manager.get("sua.chave") em qualquer módulo

    Nenhum outro arquivo Python precisa ser modificado.
    """

    def __init__(self) -> None:
        self._config: Dict[str, dict]           = {}
        self._cache:  Dict[str, pygame.Surface] = {}
        self._fallback: Optional[pygame.Surface] = None
        self._config_loaded = False

    #
    # Carregamento de configuração
    #
    def load_config(self) -> None:
        """
        Lê assets/data/sprites.json e mescla com o fallback interno.
        Chamado automaticamente na primeira chamada a get().
        Pode ser chamado manualmente para recarregar em runtime.
        """
        config: Dict[str, dict] = {}

        # Tenta JSON externo
        if _JSON_CONFIG.is_file():
            try:
                raw = _JSON_CONFIG.read_text(encoding="utf-8")
                data = json.loads(raw)
                for key, val in data.items():
                    if key.startswith("_"):        # ignora comentários
                        continue
                    if isinstance(val, dict):
                        config[key] = val
                logger.info("SpriteManager: %d sprites carregados de %s",
                            len(config), _JSON_CONFIG.name)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("SpriteManager: falha ao ler JSON (%s). "
                               "Usando configuração interna.", exc)
        else:
            logger.warning("SpriteManager: %s não encontrado. "
                           "Usando configuração interna.", _JSON_CONFIG)

        # Mescla com fallback interno (Python dict) — JSON tem prioridade
        for key, val in _FALLBACK_CONFIG.items():
            if key not in config:
                config[key] = val

        self._config        = config
        self._config_loaded = True

    #
    # Fallback visual
    #
    def _get_fallback(self) -> pygame.Surface:
        """
        Retorna Surface de fallback: círculo cinza semitransparente 28×28.
        Criado uma única vez e reutilizado.
        """
        if self._fallback is None:
            s = pygame.Surface((28, 28), pygame.SRCALPHA)
            pygame.draw.circle(s, (160, 160, 160, 200), (14, 14), 12)
            pygame.draw.circle(s, (220, 220, 220, 200), (14, 14), 12, 2)
            self._fallback = s
        return self._fallback

    #
    # Carregamento de arquivo
    #
    def _load_surface(self, path: str,
                      cfg: dict) -> Optional[pygame.Surface]:
        """
        Carrega um arquivo de imagem, aplica escala e opacidade.

        Parâmetros:
            path — caminho relativo à raiz do projeto
            cfg  — dicionário de configuração do sprite

        Retorna:
            pygame.Surface processada, ou None em caso de falha.
        """
        abs_path = (_ROOT / path) if not os.path.isabs(path) else Path(path)
        if not abs_path.is_file():
            logger.debug("SpriteManager: arquivo não encontrado: %s", abs_path)
            return None

        try:
            img = pygame.image.load(str(abs_path))
            # Converter superfície para o formato do display (melhor performance)
            if img.get_flags() & pygame.SRCALPHA:
                img = img.convert_alpha()
            else:
                img = img.convert()

            # Redimensionamento
            w, h    = img.get_size()
            scale   = float(cfg.get("scale", 1.0))
            tgt_w   = int(cfg["width"])  if cfg.get("width")  else int(w * scale)
            tgt_h   = int(cfg["height"]) if cfg.get("height") else int(h * scale)
            if (tgt_w, tgt_h) != (w, h):
                img = pygame.transform.smoothscale(img, (tgt_w, tgt_h))

            # Opacidade global
            opacity = int(cfg.get("opacity", 255))
            if opacity < 255:
                img.set_alpha(opacity)

            return img

        except (pygame.error, OSError, ValueError) as exc:
            logger.warning("SpriteManager: erro ao carregar %s — %s", path, exc)
            return None

    #
    # API pública principal
    #
    def get(self, key: str) -> pygame.Surface:
        """
        Retorna o sprite correspondente à chave.

        Carrega e armazena em cache na primeira chamada.
        Retorna fallback cinza se o arquivo não existir ou não puder ser lido.

        Parâmetros:
            key — identificador do sprite (ex.: "powerup.speed")

        Retorna:
            pygame.Surface pronta para blit.
        """
        if not self._config_loaded:
            self.load_config()

        if key in self._cache:
            return self._cache[key]

        cfg    = self._config.get(key, {})
        path   = cfg.get("path")
        surface: Optional[pygame.Surface] = None

        if path:
            surface = self._load_surface(path, cfg)

        if surface is None:
            surface = self._get_fallback()
            if path:
                logger.debug("SpriteManager: usando fallback para '%s'", key)

        self._cache[key] = surface
        return surface

    def get_scaled(self, key: str, width: int, height: int) -> pygame.Surface:
        """
        Retorna o sprite redimensionado para as dimensões informadas.

        Usa cache separado por dimensão para evitar rescaling repetido.

        Parâmetros:
            key    — identificador do sprite
            width  — largura alvo em pixels
            height — altura alvo em pixels

        Retorna:
            pygame.Surface redimensionada.
        """
        cache_key = f"{key}_{width}x{height}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        base   = self.get(key)
        scaled = pygame.transform.smoothscale(base, (width, height))
        self._cache[cache_key] = scaled
        return scaled

    def get_animation(self, anim_key: str) -> Optional[AnimationState]:
        """
        Cria e retorna um AnimationState para a chave de animação informada.

        Divide o sprite horizontalmente em N quadros iguais se frames > 1.
        Retorna None se a chave não existir na configuração.

        Parâmetros:
            anim_key — chave do sprite com frames > 1 configurados

        Retorna:
            AnimationState ou None.
        """
        if not self._config_loaded:
            self.load_config()

        cfg = self._config.get(anim_key)
        if not cfg:
            return None

        base     = self.get(anim_key)
        fps      = float(cfg.get("fps",    0))
        loop     = bool(cfg.get("loop",    True))
        n_frames = int(cfg.get("frames",   1))

        if n_frames > 1:
            w, h      = base.get_size()
            frame_w   = w // n_frames
            frames    = [
                base.subsurface(pygame.Rect(i * frame_w, 0, frame_w, h)).copy()
                for i in range(n_frames)
            ]
        else:
            frames = [base]

        return AnimationState(frames, fps, loop)

    #
    # Utilitários
    #
    def preload(self, keys: List[str]) -> None:
        """
        Pré-carrega uma lista de sprites em cache.

        Chame antes do loop principal para evitar travamentos em runtime.

        Parâmetros:
            keys — lista de chaves a pré-carregar
        """
        for key in keys:
            self.get(key)
        logger.info("SpriteManager: %d sprites pré-carregados.", len(keys))

    def invalidate(self, key: str) -> None:
        """
        Remove uma entrada do cache, forçando recarregamento na próxima chamada.

        Parâmetros:
            key — chave a invalidar (também invalida versões escaladas)
        """
        to_remove = [k for k in self._cache if k == key or k.startswith(f"{key}_")]
        for k in to_remove:
            del self._cache[k]

    def clear_cache(self) -> None:
        """Remove todo o cache de sprites."""
        self._cache.clear()
        logger.info("SpriteManager: cache limpo.")

    def reload_config(self) -> None:
        """
        Recarrega sprites.json e limpa o cache.
        Útil para hot-reload de sprites em desenvolvimento.
        """
        self._config_loaded = False
        self.clear_cache()
        self.load_config()

    def list_sprites(self, categoria: Optional[str] = None) -> List[str]:
        """
        Lista todas as chaves de sprites registradas.

        Parâmetros:
            categoria — filtra por categoria (ex.: "powerup", "player")

        Retorna:
            Lista de chaves ordenadas alfabeticamente.
        """
        if not self._config_loaded:
            self.load_config()
        if categoria:
            return sorted(k for k, v in self._config.items()
                          if v.get("categoria") == categoria)
        return sorted(self._config.keys())


#
# Instância global — importar e usar diretamente em qualquer módulo
#
sprite_manager = SpriteManager()
