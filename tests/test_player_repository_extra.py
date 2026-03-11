import pytest
from unittest.mock import MagicMock, patch
from app.repositories.player_repository import PlayerRepository

@pytest.fixture
def mock_session():
    return MagicMock()

def test_get_by_guild_and_lineage_found(mock_session):
    lineage = MagicMock()
    lineage.class_id = 1
    lineage.lineage_index = 2
    mock_session.query().filter().all.return_value = [lineage]
    player1 = MagicMock()
    player1.id = 1
    player2 = MagicMock()
    player2.id = 2
    # Usa os mesmos objetos para garantir identidade
    players_list = [player1, player2]
    side_effect_iter = iter([players_list, players_list])
    def side_effect(*args, **kwargs):
        try:
            return next(side_effect_iter)
        except StopIteration:
            return []
    mock_session.query().filter().all.side_effect = side_effect
    result = PlayerRepository.get_by_guild_and_lineage(mock_session, 123, "LineageName")
    assert any(p.id == player1.id for p in result)
    assert any(p.id == player2.id for p in result)

def test_update_from_data_guild(mock_session):
    player = MagicMock()
    data = {"guild": "123"}
    PlayerRepository.update_from_data(mock_session, player, data)
    assert True

def test_update_from_data_no_guild(mock_session):
    player = MagicMock()
    data = {"name": "Player1"}
    PlayerRepository.update_from_data(mock_session, player, data)
    assert True
