import pytest
from unittest.mock import patch, MagicMock
from app.services.sync_service import SyncService

def test_sync_all_runs():
    with patch('app.services.sync_service.SessionLocal') as session_mock:
        session = MagicMock()
        session_mock.return_value = session
        session.begin.return_value.__enter__.return_value = session
        session.begin.return_value.__exit__.return_value = None
        with patch('app.services.sync_service.requests.post') as post_mock, \
             patch('app.services.sync_service.requests.get') as get_mock, \
             patch('app.services.sync_service.LevelRepository.clear') as level_clear_mock, \
             patch('app.services.sync_service.ArenaRepository.clear_category') as arena_clear_mock, \
             patch('app.services.sync_service.PlayerRepository.get_or_create') as get_or_create_mock, \
             patch('app.services.sync_service.PlayerRepository.update_from_data') as update_mock, \
             patch('app.services.sync_service.LevelRepository.save') as level_save_mock, \
             patch('app.services.sync_service.ArenaRepository.save') as arena_save_mock:
            post_mock.return_value.json.return_value = [{"name": "Player1", "guild": "GuildX"}]
            get_mock.return_value.json.return_value = [{"charName": "Player1"}]
            session.execute.return_value.scalar.return_value = 1
            SyncService.sync_all()
            level_clear_mock.assert_called_once()
            arena_clear_mock.assert_any_call(session, "champion")
            arena_clear_mock.assert_any_call(session, "aspirant")
            level_save_mock.assert_called()
            arena_save_mock.assert_called()
