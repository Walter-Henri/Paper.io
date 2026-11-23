"""
test_sprite_manager.py — TerritórIO: Edição Brasil
-----------------------------------------------------
Testes para src/systems/sprite_manager.py.

Cobre:
    - Carregamento do arquivo JSON de configuração
    - Retorno de fallback para chaves inexistentes
    - Cache: segunda chamada não relê arquivo
    - Escalonamento com get_scaled
    - Invalidação de cache
    - Listagem de sprites por categoria
    - Inicialização segura sem display pygame

Execute com:
    python -m pytest tests/test_sprite_manager.py -v
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import pygame

# Inicializa pygame em modo headless antes de qualquer import que use Surface
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame.init()
pygame.display.set_mode((1, 1))


from src.systems.sprite_manager import SpriteManager


# ---------------------------------------------------------------------------
# Fixture: instância isolada por teste (não usa a singleton global)
# ---------------------------------------------------------------------------

@pytest.fixture
def sm() -> SpriteManager:
    """SpriteManager isolado (não usa instância global)."""
    manager = SpriteManager()
    manager.load_config()
    return manager


# ---------------------------------------------------------------------------
# Carregamento de configuração
# ---------------------------------------------------------------------------

class TestConfigLoading:
    def test_config_loads_without_error(self, sm: SpriteManager):
        """load_config não deve lançar exceção."""
        sm2 = SpriteManager()
        sm2.load_config()   # segunda chamada deve ser idempotente

    def test_config_contains_powerup_keys(self, sm: SpriteManager):
        """Chaves dos 5 power-ups devem estar presentes."""
        for key in ["powerup.size_up", "powerup.speed",
                    "powerup.bomb",    "powerup.shield", "powerup.eagle"]:
            assert key in sm._config, f"Chave '{key}' ausente na configuração"

    def test_config_contains_player_key(self, sm: SpriteManager):
        """Chave do jogador deve existir."""
        assert "player.default" in sm._config

    def test_config_contains_bot_key(self, sm: SpriteManager):
        """Chave do bot deve existir."""
        assert "bot.default" in sm._config


# ---------------------------------------------------------------------------
# get() — retorno e cache
# ---------------------------------------------------------------------------

class TestGet:
    def test_get_returns_surface(self, sm: SpriteManager):
        """get() deve retornar pygame.Surface para qualquer chave."""
        surf = sm.get("player.default")
        assert isinstance(surf, pygame.Surface)

    def test_get_unknown_key_returns_fallback(self, sm: SpriteManager):
        """Chave inexistente deve retornar Surface de fallback, não lançar exceção."""
        surf = sm.get("chave.que.nao.existe")
        assert isinstance(surf, pygame.Surface)

    def test_get_caches_result(self, sm: SpriteManager):
        """Segunda chamada a get() deve retornar o mesmo objeto (cache)."""
        s1 = sm.get("player.default")
        s2 = sm.get("player.default")
        assert s1 is s2

    def test_fallback_has_nonzero_size(self, sm: SpriteManager):
        """Surface de fallback deve ter dimensões > 0."""
        surf = sm.get("chave.inexistente.xyz")
        w, h = surf.get_size()
        assert w > 0 and h > 0


# ---------------------------------------------------------------------------
# get_scaled()
# ---------------------------------------------------------------------------

class TestGetScaled:
    def test_scaled_dimensions(self, sm: SpriteManager):
        """get_scaled deve retornar Surface com as dimensões solicitadas."""
        surf = sm.get_scaled("player.default", 64, 64)
        assert surf.get_size() == (64, 64)

    def test_scaled_caches_by_dimensions(self, sm: SpriteManager):
        """Duas chamadas com as mesmas dimensões devem retornar o mesmo objeto."""
        s1 = sm.get_scaled("player.default", 32, 32)
        s2 = sm.get_scaled("player.default", 32, 32)
        assert s1 is s2

    def test_scaled_different_sizes_different_objects(self, sm: SpriteManager):
        """Dimensões diferentes devem produzir objetos diferentes."""
        s1 = sm.get_scaled("player.default", 32, 32)
        s2 = sm.get_scaled("player.default", 64, 64)
        assert s1 is not s2


# ---------------------------------------------------------------------------
# invalidate() e clear_cache()
# ---------------------------------------------------------------------------

class TestCacheManagement:
    def test_invalidate_forces_reload(self, sm: SpriteManager):
        """Após invalidate, get() deve retornar novo objeto."""
        s1 = sm.get("player.default")
        sm.invalidate("player.default")
        s2 = sm.get("player.default")
        # Podem ser iguais em conteúdo, mas devem ser objetos distintos
        assert s1 is not s2

    def test_clear_cache_empties_all(self, sm: SpriteManager):
        """clear_cache deve esvaziar completamente o cache."""
        sm.get("player.default")
        sm.get("bot.default")
        sm.clear_cache()
        assert len(sm._cache) == 0


# ---------------------------------------------------------------------------
# list_sprites()
# ---------------------------------------------------------------------------

class TestListSprites:
    def test_list_all_returns_list(self, sm: SpriteManager):
        """list_sprites() sem argumento deve retornar lista."""
        result = sm.list_sprites()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_list_by_category(self, sm: SpriteManager):
        """list_sprites('powerup') deve retornar apenas chaves de powerup."""
        result = sm.list_sprites("powerup")
        assert all("powerup." in key for key in result)

    def test_list_sorted(self, sm: SpriteManager):
        """Resultado deve estar em ordem alfabética."""
        result = sm.list_sprites()
        assert result == sorted(result)
