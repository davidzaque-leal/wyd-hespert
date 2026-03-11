import pytest
from unittest.mock import MagicMock, patch
from app.repositories.level_repository import LevelRepository

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def mock_player():
    player = MagicMock()
    player.id = 1
    player.class_id = 1
    player.class_lineage = 2
    player.subclass = 3
    player.subclass_lineage = 4
    return player

def test_clear(mock_session):
    LevelRepository.clear(mock_session)
    mock_session.query().delete.assert_called_once()

def test_save(mock_session, mock_player):
    ranking_data = {
        "points": 10,
        "level": 5,
        "levelSub": 2,
        "Soma Level": 7
    }
    with patch('app.repositories.level_repository.ClassLineage'):
        LevelRepository.save(mock_session, mock_player, ranking_data)
        mock_session.add.assert_called_once()

def test_get_all(mock_session):
    ranking = MagicMock()
    ranking.player = MagicMock()
    ranking.player.class_id = 1
    ranking.player.class_lineage = 2
    ranking.player.subclass = 3
    ranking.player.subclass_lineage = 4
    ranking.celestial_lineage_name = None
    ranking.subclass_lineage_name = None
    mock_session.query().options().order_by().all.return_value = [ranking]
    with patch('app.repositories.level_repository.ClassLineage'):
        result = LevelRepository.get_all(mock_session)
        assert isinstance(result, list)
