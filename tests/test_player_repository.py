import pytest
from unittest.mock import MagicMock, patch
from app.repositories.player_repository import PlayerRepository

@pytest.fixture
def mock_session():
    return MagicMock()

def test_get_or_create_existing(mock_session):
    player_data = {"name": "Player1"}
    player = MagicMock()
    mock_session.query().filter().first.return_value = player
    with patch.object(PlayerRepository, 'update_from_data') as update_mock:
        result = PlayerRepository.get_or_create(mock_session, player_data)
        assert result == player
        update_mock.assert_called_once()

def test_get_or_create_new(mock_session):
    player_data = {"name": "Player2"}
    mock_session.query().filter().first.return_value = None
    with patch.object(PlayerRepository, 'update_from_data') as update_mock:
        with patch('app.repositories.player_repository.Player') as PlayerMock:
            player_instance = PlayerMock.return_value
            result = PlayerRepository.get_or_create(mock_session, player_data)
            assert result == player_instance
            update_mock.assert_called_once()
            mock_session.add.assert_called_once_with(player_instance)
            mock_session.flush.assert_called_once()

def test_get_by_name(mock_session):
    mock_session.query().filter().first.return_value = "player"
    result = PlayerRepository.get_by_name(mock_session, "Player1")
    assert result == "player"

def test_get_by_lineage(mock_session):
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
    result = PlayerRepository.get_by_lineage(mock_session, "LineageName")
    assert any(p.id == player1.id for p in result)
    assert any(p.id == player2.id for p in result)

def test_get_by_guild_id(mock_session):
    mock_session.query().filter().all.return_value = ["player"]
    result = PlayerRepository.get_by_guild_id(mock_session, 123)
    assert result == ["player"]
