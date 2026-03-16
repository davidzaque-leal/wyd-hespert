import pytest
from unittest.mock import MagicMock, patch
from app.services import ranking_history_service


def test_get_formatted_now():
    now = ranking_history_service.get_formatted_now()
    assert isinstance(now, str)


def test_get_arena_number_by_time():
    from datetime import datetime
    assert ranking_history_service.get_arena_number_by_time(datetime.strptime('2026-03-10 13:31', '%Y-%m-%d %H:%M')) == 1
    assert ranking_history_service.get_arena_number_by_time(datetime.strptime('2026-03-10 19:31', '%Y-%m-%d %H:%M')) == 2
    assert ranking_history_service.get_arena_number_by_time(datetime.strptime('2026-03-10 21:01', '%Y-%m-%d %H:%M')) == 3
    assert ranking_history_service.get_arena_number_by_time(datetime.strptime('2026-03-10 23:31', '%Y-%m-%d %H:%M')) == 4
    assert ranking_history_service.get_arena_number_by_time(datetime.strptime('2026-03-10 00:00', '%Y-%m-%d %H:%M')) == 4
