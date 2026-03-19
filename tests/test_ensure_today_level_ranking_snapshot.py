import pytest
from unittest.mock import MagicMock, patch
from app.services.ranking_history_service import ensure_today_level_ranking_snapshot

@pytest.fixture
def mock_session():
    return MagicMock()

def test_ensure_today_level_ranking_snapshot_exists(mock_session):
    # Simula snapshot já existente
    mock_session.query.return_value.scalar.return_value = True
    result = ensure_today_level_ranking_snapshot(mock_session)
    assert result is True
    mock_session.bulk_save_objects.assert_not_called()
    mock_session.commit.assert_not_called()

def test_ensure_today_level_ranking_snapshot_creates(mock_session):
    # Simula snapshot inexistente
    mock_session.query.return_value.scalar.return_value = False
    result = ensure_today_level_ranking_snapshot(mock_session)
    assert result is False

def test_ensure_today_level_ranking_snapshot_no_data(mock_session):
    # Simula snapshot inexistente e ranking vazio
    mock_session.query.return_value.scalar.return_value = False
    mock_session.query.return_value.options.return_value.order_by.return_value.all.return_value = []
    result = ensure_today_level_ranking_snapshot(mock_session)
    assert result is False
    mock_session.bulk_save_objects.assert_not_called()
    mock_session.commit.assert_not_called()
