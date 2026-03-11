import pytest
from unittest.mock import MagicMock, patch
from app.services import ranking_history_service

@pytest.fixture
def mock_session():
    return MagicMock()

def test_save_level_ranking_history_existing_today(mock_session):
    mock_session.query().filter().first.return_value = True
    result = ranking_history_service.save_level_ranking_history(mock_session, [])
    assert result is True

def test_save_level_ranking_history_exception(mock_session):
    mock_session.query().filter().first.side_effect = Exception("DB error")
    result = ranking_history_service.save_level_ranking_history(mock_session, [])
    assert result is False

def test_save_arena_ranking_history_existing_arena(mock_session):
    mock_session.query().filter().first.return_value = True
    with patch('app.services.ranking_history_service.get_arena_number_by_time', return_value=2):
        result = ranking_history_service.save_arena_ranking_history(mock_session, [], 'champion')
        assert result is True

def test_save_arena_ranking_history_exception(mock_session):
    mock_session.query().filter().first.side_effect = Exception("DB error")
    with patch('app.services.ranking_history_service.get_arena_number_by_time', return_value=2):
        result = ranking_history_service.save_arena_ranking_history(mock_session, [], 'champion')
        assert result is False
