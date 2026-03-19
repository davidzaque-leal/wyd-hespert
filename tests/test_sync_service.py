def test_check_hashes_calls_sync_all_when_hash_changes():
    with patch('app.services.sync_service.HashManager.check_and_update_hash') as hash_mock, \
        patch('app.services.sync_service.requests.get') as get_mock, \
        patch.object(SyncService, 'sync_all') as sync_all_mock:
        # Simula mudança de hash
        hash_mock.side_effect = [True, False]
        get_mock.return_value.json.return_value = [{"charName": "Player1"}]
        SyncService.check_hashes()
        sync_all_mock.assert_called_once()

def test_check_hashes_does_not_call_sync_all_when_no_hash_changes():
    with patch('app.services.sync_service.HashManager.check_and_update_hash') as hash_mock, \
        patch('app.services.sync_service.requests.get') as get_mock, \
        patch.object(SyncService, 'sync_all') as sync_all_mock:
        # Nenhuma mudança de hash
        hash_mock.side_effect = [False, False]
        get_mock.return_value.json.return_value = [{"charName": "Player1"}]
        SyncService.check_hashes()
        sync_all_mock.assert_not_called()
import pytest
from unittest.mock import patch, MagicMock
from app.services.sync_service import SyncService
