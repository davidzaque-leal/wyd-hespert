import pytest
from unittest.mock import MagicMock, patch
import datetime
from app.services import ranking_history_service

def test_get_brasilia_now():
    now = ranking_history_service.get_brasilia_now()
    assert isinstance(now, datetime.datetime)

def test_get_brasilia_date():
    date = ranking_history_service.get_brasilia_date()
    assert isinstance(date, datetime.date)

def test_get_arena_number_by_time():
    with patch('app.services.ranking_history_service.get_brasilia_now') as mock_now:
        # Arena 1: 13:31
        mock_now.return_value = datetime.datetime(2026, 3, 10, 13, 31)
        assert ranking_history_service.get_arena_number_by_time() == 1
        # Arena 2: 19:31
        mock_now.return_value = datetime.datetime(2026, 3, 10, 19, 31)
        assert ranking_history_service.get_arena_number_by_time() == 2
        # Arena 3: 21:01
        mock_now.return_value = datetime.datetime(2026, 3, 10, 21, 1)
        assert ranking_history_service.get_arena_number_by_time() == 3
        # Arena 4: 23:31
        mock_now.return_value = datetime.datetime(2026, 3, 10, 23, 31)
        assert ranking_history_service.get_arena_number_by_time() == 4
        # Fora de janela, retorna arena mais recente
        mock_now.return_value = datetime.datetime(2026, 3, 10, 0, 0)
        assert ranking_history_service.get_arena_number_by_time() == 1
