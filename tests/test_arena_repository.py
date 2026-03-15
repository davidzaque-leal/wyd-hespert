import pytest
from unittest.mock import MagicMock
from app.repositories.arena_repository import ArenaRepository
from app.models import ArenaCategoryEnum

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def mock_player():
    player = MagicMock()
    player.id = 1
    return player

def test_clear_category(mock_session):
    ArenaRepository.clear_category(mock_session, ArenaCategoryEnum.champion)
    mock_session.query().filter().delete.assert_called_once()

def test_save_arena(mock_session, mock_player):
    arena_data = {
        "registerCount": 2,
        "killValue": 5,
        "deathValue": 1,
        "winCount": 3,
        "points": 10,
        "bonusKill": 0,
        "total": 21
    }
    ArenaRepository.save(mock_session, mock_player, arena_data, ArenaCategoryEnum.champion)
    mock_session.add.assert_called_once()
