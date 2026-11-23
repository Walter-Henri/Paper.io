# Responsabilidade:
# Carregar e reproduzir efeitos sonoros do jogo.
# Carrega sons Kenney (CC0) de disco e gera SFX procedurais via numpy.
# Expõe interface simples: play(nome), toggle(), set_volume(v).
# Não contém lógica de jogo, renderização ou comportamento de entidades.

from __future__ import annotations
import os
import numpy as np
import pygame
from typing import Dict

_ROOT      = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_AUDIO_DIR = os.path.join(_ROOT, "assets", "audio")


def _tone(freq: float, duration: float, volume: float = 0.3,
          sample_rate: int = 22050, wave: str = "sine",
          decay: bool = True) -> pygame.mixer.Sound:
    n = int(sample_rate * duration)
    t = np.linspace(0, duration, n, False)
    if wave == "square":
        data = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave == "saw":
        data = 2 * (t * freq - np.floor(0.5 + t * freq))
    else:
        data = np.sin(2 * np.pi * freq * t)
    if decay:
        data = data * (np.linspace(1.0, 0.0, n) ** 1.4)
    audio  = (data * volume * 32767).astype(np.int16)
    stereo = np.column_stack((audio, audio))
    return pygame.sndarray.make_sound(stereo)


class AudioManager:
    def __init__(self):
        self.enabled = True
        self.volume  = 0.55
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        except Exception:
            self.enabled = False
            return
        self._load()

    def _load(self) -> None:
        # Sons baseados em arquivo (Kenney CC0)
        file_sounds = {
            "click":  "click-a.ogg",
            "click2": "click-b.ogg",
            "switch": "switch-a.ogg",
            "tap":    "tap-a.ogg",
        }
        for key, fname in file_sounds.items():
            path = os.path.join(_AUDIO_DIR, fname)
            if os.path.isfile(path):
                try:
                    self.sounds[key] = pygame.mixer.Sound(path)
                except Exception:
                    pass

        # SFX procedurais (eventos de jogo)
        try:
            self.sounds["claim"]   = _tone(520, 0.11, 0.32)
            self.sounds["claim2"]  = _tone(760, 0.09, 0.22)
            self.sounds["death"]   = _tone(110, 0.38, 0.38, wave="saw")
            self.sounds["kill"]    = _tone(360, 0.14, 0.32, wave="square")
            self.sounds["start"]   = _tone(440, 0.16, 0.28)
            self.sounds["victory"] = _tone(660, 0.25, 0.30)
        except Exception:
            pass

    def play(self, name: str) -> None:
        if not self.enabled:
            return
        s = self.sounds.get(name)
        if s:
            s.set_volume(self.volume)
            s.play()

    def set_volume(self, v: float) -> None:
        self.volume = max(0.0, min(1.0, v))

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled
