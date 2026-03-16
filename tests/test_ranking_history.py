import pytest
from app.services import ranking_history_service

def test_get_level_changes_no_snapshot():
    session = MagicMock()
    session.query().filter().first.return_value = None
    result = ranking_history_service.get_level_changes(session, "TestPlayer", {"level_celestial": 100, "level_sub_celestial": 50})
    assert result['celestial_change'] == 0
    assert result['subclass_change'] == 0
    assert result['celestial_arrow'] == ''
    assert result['subclass_arrow'] == ''

def test_get_level_changes_with_snapshot():
    session = MagicMock()
    mock_record = MagicMock()
    mock_record.level_celestial = 90
    mock_record.level_sub_celestial = 40
    session.query().filter().first.return_value = mock_record
    result = ranking_history_service.get_level_changes(session, "TestPlayer", {"level_celestial": 100, "level_sub_celestial": 50})
    assert result['celestial_change'] == 10
    assert result['subclass_change'] == 10
    assert result['celestial_arrow'] == '↑'
    assert result['subclass_arrow'] == '↑'

def test_get_position_changes_no_snapshot():
    session = MagicMock()
    session.query().filter().first.return_value = None
    result = ranking_history_service.get_position_changes(session, "TestPlayer", 1)
    assert result['position_change'] == 0
    assert result['arrow'] == ''
    assert result['active'] is False

def test_get_position_changes_with_snapshot():
    session = MagicMock()
    mock_record = MagicMock()
    mock_record.rank_position = 3
    session.query().filter().first.return_value = mock_record
    result = ranking_history_service.get_position_changes(session, "TestPlayer", 1)
    assert result['position_change'] == 2
    assert result['arrow'] == '↑'
    assert result['active'] is True

def test_save_arena_ranking_history_error():
    session = MagicMock()
    session.query().filter().first.side_effect = Exception("DB error")
    result = ranking_history_service.save_arena_ranking_history(session, [], "champion")
    assert result is False

def test_save_level_ranking_history_error():
    session = MagicMock()
    session.query().filter().first.side_effect = Exception("DB error")
    result = ranking_history_service.save_level_ranking_history(session, [])
    assert result is False
import unittest
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta

from app.models import ArenaRanking, LevelRanking, Player
from app.services.ranking_history_service import (
    save_arena_ranking_history,
    save_level_ranking_history,
    get_arena_number_by_time,
)

class TestRankingHistory(unittest.TestCase):
    def setUp(self):
        self.session = MagicMock()
        self.player = Player(id=1, name="TestPlayer")

    def test_arena_ranking_history_single_category(self):
        # Simula dados de ranking de arena para champion
        players_data = [
            {"id": 1, "charName": "TestPlayer", "total": 100, "points": 50, "winCount": 10, "killValue": 20, "deathValue": 5}
        ]
        category = "champion"
        # Simula não existir registro hoje
        self.session.query().filter().first.return_value = None
        result = save_arena_ranking_history(self.session, players_data, category)
        self.assertTrue(result)
        self.session.add.assert_called()
        self.session.commit.assert_called()

    def test_arena_ranking_history_duplicate(self):
        # Simula já existir registro hoje
        self.session.query().filter().first.return_value = True
        players_data = [
            {"id": 1, "charName": "TestPlayer", "total": 100, "points": 50, "winCount": 10, "killValue": 20, "deathValue": 5}
        ]
        category = "champion"
        result = save_arena_ranking_history(self.session, players_data, category)
        self.assertTrue(result)
        self.session.add.assert_not_called()

    def test_level_ranking_history_single_day(self):
        # Simula dados de ranking de level
        players_data = [
            {"id": 1, "name": "TestPlayer", "Soma Level": 200, "points": 80, "celestial_lineage": "A", "subclass_lineage": "B"}
        ]
        # Simula não existir registro hoje
        self.session.query().filter().first.return_value = None
        result = save_level_ranking_history(self.session, players_data)
        self.assertTrue(result)
        self.session.add.assert_called()
        self.session.commit.assert_called()

    def test_level_ranking_history_duplicate(self):
        # Simula já existir registro hoje
        self.session.query().filter().first.return_value = True
        players_data = [
            {"id": 1, "name": "TestPlayer", "Soma Level": 200, "points": 80, "level": 100, "levelSub": 50, "celestial_lineage": "A", "subclass_lineage": "B"}
        ]
        result = save_level_ranking_history(self.session, players_data)
        self.assertTrue(result)
        self.session.add.assert_not_called()

def test_get_arena_number_by_time_pytest(monkeypatch):
    from app.services import ranking_history_service
    from datetime import datetime
    assert ranking_history_service.get_arena_number_by_time(datetime.strptime('2026-03-10 13:31', '%Y-%m-%d %H:%M')) == 1

if __name__ == '__main__':
    unittest.main()
