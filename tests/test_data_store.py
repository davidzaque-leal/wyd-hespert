import os
import json
import pytest
from app.services.data_store import DataStore
from unittest.mock import patch, MagicMock
def test_save_and_load_backup(tmp_path, data_store):
    # Prepara dados
    data_store.level_ranking = [{'name': 'A', 'Soma Level': 10}]
    data_store.arena_champion = [{'charName': 'A', 'total': 5, 'winCount': 2}]
    data_store.arena_aspirant = [{'charName': 'B', 'total': 3, 'winCount': 1}]
    data_store.last_update = '2026-03-10 10:00:00'
    # Usa backup temporário
    backup_file = tmp_path / "data_backup.json"
    data_store.backup_file = str(backup_file)
    data_store._save_backup()
    # Limpa dados e recarrega
    data_store.level_ranking = []
    data_store.arena_champion = []
    data_store.arena_aspirant = []
    data_store.last_update = None
    data_store._load_backup()
    assert data_store.level_ranking == [{'name': 'A', 'Soma Level': 10}]
    assert data_store.arena_champion == [{'charName': 'A', 'total': 5, 'winCount': 2}]
    assert data_store.arena_aspirant == [{'charName': 'B', 'total': 3, 'winCount': 1}]
    assert data_store.last_update == '2026-03-10 10:00:00'

def test_get_combined_ranking(data_store):
    data_store.level_ranking = [
        {'name': 'A', 'Soma Level': 10},
        {'name': 'B', 'Soma Level': 5}
    ]
    data_store.arena_champion = [
        {'charName': 'A', 'total': 7, 'winCount': 3},
        {'charName': 'B', 'total': 2, 'winCount': 1}
    ]
    combined = data_store.get_combined_ranking()
    assert combined[0]['name'] == 'A'
    assert combined[0]['arena_points'] == 7
    assert combined[0]['level_total'] == 10
    assert combined[0]['wins'] == 3
    assert combined[1]['name'] == 'B'
    assert combined[1]['arena_points'] == 2
    assert combined[1]['level_total'] == 5
    assert combined[1]['wins'] == 1

@patch('app.services.data_store.SessionLocal')
def test_update_data_handles_db_error(mock_session_local, data_store):
    mock_session_local.side_effect = Exception("DB error")
    # Não deve lançar exceção
    data_store.update_data(sync=False)

def test_update_data_without_sync(data_store):
    # Não deve chamar sync nem salvar histórico
    with patch('app.services.data_store.SyncService.sync_all') as sync_mock:
        with patch('app.services.data_store.save_level_ranking_history') as save_level_mock:
            with patch('app.services.data_store.save_arena_ranking_history') as save_arena_mock:
                data_store.level_ranking = []
                data_store.arena_champion = []
                data_store.arena_aspirant = []
                data_store.update_data(sync=False)
                sync_mock.assert_not_called()
                save_level_mock.assert_not_called()
                save_arena_mock.assert_not_called()
import pytest
from app.services.data_store import DataStore
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_db():
    with patch('app.services.data_store.SessionLocal') as mock_session_local:
        session = MagicMock()
        mock_session_local.return_value = session
        yield session

@pytest.fixture
def data_store():
    return DataStore()

@patch('app.services.data_store.LevelRepository')
@patch('app.services.data_store.PlayerSerializer')
def test_update_data_reads_champion_and_aspirant(mock_serializer, mock_level_repo, mock_db, data_store):
    # Setup mock DB rows
    champion_row = MagicMock()
    champion_row.category = 'champion'
    champion_row.player.name = 'Player1'
    aspirant_row = MagicMock()
    aspirant_row.category = 'aspirant'
    aspirant_row.player.name = 'Player2'

    mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.side_effect = [
        [champion_row], [aspirant_row]
    ]
    mock_level_repo.get_all.return_value = []
    mock_serializer.serialize_arena_ranking.side_effect = lambda r: {'charName': r.player.name, 'category': r.category}

    data_store.update_data(sync=False)

    assert data_store.arena_champion == [{'charName': 'Player1', 'category': 'champion'}]
    assert data_store.arena_aspirant == [{'charName': 'Player2', 'category': 'aspirant'}]

@patch('app.services.data_store.LevelRepository')
@patch('app.services.data_store.PlayerSerializer')
def test_update_data_no_sync(mock_serializer, mock_level_repo, mock_db, data_store):
    mock_level_repo.get_all.return_value = []
    mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.side_effect = [[], []]
    data_store.update_data(sync=False)
    assert data_store.level_ranking == []
    assert data_store.arena_champion == []
    assert data_store.arena_aspirant == []

@patch('app.services.data_store.SyncService')
def test_update_data_sync_calls_sync_service(mock_sync_service, mock_db, data_store):
    mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.side_effect = [[], []]
    data_store.update_data(sync=True)
    mock_sync_service.sync_all.assert_called_once()
