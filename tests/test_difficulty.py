"""
test_difficulty.py — TerritórIO: Edição Brasil
-------------------------------------------------
Testes para src/config/difficulty.py.

Cobre:
    - Existência dos três níveis obrigatórios
    - Coerência dos parâmetros (tipos, intervalos válidos)
    - Função get_profile com nome válido e inválido
    - Ordenação lógica: fácil < médio < difícil em agressividade

Execute com:
    python -m pytest tests/test_difficulty.py -v
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from src.config.difficulty import DIFFICULTIES, DifficultyProfile, get_profile


class TestDifficultiesExist:
    def test_three_levels_present(self):
        """Os três níveis obrigatórios devem existir."""
        assert "facil"   in DIFFICULTIES
        assert "medio"   in DIFFICULTIES
        assert "dificil" in DIFFICULTIES

    def test_all_values_are_profiles(self):
        """Todos os valores devem ser instâncias de DifficultyProfile."""
        for name, prof in DIFFICULTIES.items():
            assert isinstance(prof, DifficultyProfile), (
                f"'{name}' não é DifficultyProfile"
            )


class TestProfileParameters:
    @pytest.mark.parametrize("name", ["facil", "medio", "dificil"])
    def test_speed_multiplier_positive(self, name):
        """speed_multiplier deve ser positivo."""
        assert DIFFICULTIES[name].speed_multiplier > 0

    @pytest.mark.parametrize("name", ["facil", "medio", "dificil"])
    def test_think_interval_positive(self, name):
        """think_interval deve ser positivo."""
        assert DIFFICULTIES[name].think_interval > 0

    @pytest.mark.parametrize("name", ["facil", "medio", "dificil"])
    def test_probabilities_in_range(self, name):
        """Probabilidades devem estar em [0, 1]."""
        p = DIFFICULTIES[name]
        assert 0.0 <= p.intercept_prob <= 1.0
        assert 0.0 <= p.hunt_prob      <= 1.0

    @pytest.mark.parametrize("name", ["facil", "medio", "dificil"])
    def test_priority_types_is_list(self, name):
        """priority_types deve ser uma lista."""
        assert isinstance(DIFFICULTIES[name].priority_types, list)

    @pytest.mark.parametrize("name", ["facil", "medio", "dificil"])
    def test_name_is_string(self, name):
        """name deve ser uma string não vazia."""
        assert isinstance(DIFFICULTIES[name].name, str)
        assert len(DIFFICULTIES[name].name) > 0


class TestLogicalOrdering:
    """Fácil deve ser mais passivo que difícil em todos os eixos de agressividade."""

    def test_think_interval_ordering(self):
        """Fácil pensa mais devagar que difícil."""
        assert DIFFICULTIES["facil"].think_interval > DIFFICULTIES["dificil"].think_interval

    def test_hunt_prob_ordering(self):
        """Fácil tem menor probabilidade de caçar."""
        assert DIFFICULTIES["facil"].hunt_prob < DIFFICULTIES["dificil"].hunt_prob

    def test_intercept_prob_ordering(self):
        """Fácil intercepta menos."""
        assert DIFFICULTIES["facil"].intercept_prob < DIFFICULTIES["dificil"].intercept_prob

    def test_powerup_distance_ordering(self):
        """Difícil vai mais longe buscar power-ups."""
        assert DIFFICULTIES["facil"].powerup_max_dist < DIFFICULTIES["dificil"].powerup_max_dist


class TestGetProfile:
    def test_valid_name_returns_correct_profile(self):
        """get_profile com nome válido retorna o perfil correto."""
        p = get_profile("facil")
        assert p is DIFFICULTIES["facil"]

    def test_case_insensitive(self):
        """get_profile deve ignorar capitalização."""
        assert get_profile("MEDIO")   is DIFFICULTIES["medio"]
        assert get_profile("Dificil") is DIFFICULTIES["dificil"]

    def test_invalid_name_returns_default(self):
        """Nome inválido deve retornar o perfil padrão (médio)."""
        p = get_profile("inexistente")
        assert p is DIFFICULTIES["medio"]
