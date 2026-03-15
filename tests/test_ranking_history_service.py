import pytest
from unittest.mock import MagicMock, patch
from app.services import ranking_history_service
from app.models import ArenaNumberEnum

def test_get_formatted_now():
    now = ranking_history_service.get_formatted_now()
    assert isinstance(now, str)


def test_get_arena_number_by_time():
    with patch('app.services.ranking_history_service.get_formatted_now') as mock_now:
        mock_now.return_value = '10/03/2026 13:31'
        assert ranking_history_service.get_arena_number_by_time() == ArenaNumberEnum.one.value
        mock_now.return_value = '10/03/2026 19:31'
        assert ranking_history_service.get_arena_number_by_time() == ArenaNumberEnum.two.value
        mock_now.return_value = '10/03/2026 21:01'
        assert ranking_history_service.get_arena_number_by_time() == ArenaNumberEnum.three.value
        mock_now.return_value = '10/03/2026 23:31'
        assert ranking_history_service.get_arena_number_by_time() == ArenaNumberEnum.four.value
        mock_now.return_value = '10/03/2026 00:00'
        assert ranking_history_service.get_arena_number_by_time() == ArenaNumberEnum.one.value
