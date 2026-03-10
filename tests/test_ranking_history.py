import unittest
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta

from app.models import ArenaRanking, LevelRanking, Player
from app.services.ranking_history_service import (
    save_arena_ranking_history,
    save_level_ranking_history,
    get_arena_number_by_time,
    get_brasilia_now,
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
            {"id": 1, "name": "TestPlayer", "Soma Level": 200, "points": 80, "level": 100, "levelSub": 50, "celestial_lineage": "A", "subclass_lineage": "B"}
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

    def test_get_arena_number_by_time(self):
        # Testa se retorna arena correta para horário
        original_now = get_brasilia_now
        try:
            def fake_now():
                return datetime(2026, 3, 10, 13, 31, tzinfo=timezone(timedelta(hours=-3)))
            globals()['get_brasilia_now'] = fake_now
            arena_num = get_arena_number_by_time()
            self.assertEqual(arena_num, 1)
        finally:
            globals()['get_brasilia_now'] = original_now

if __name__ == '__main__':
    unittest.main()
