import unittest
from unittest.mock import MagicMock
from app.services.ranking_history_service import get_latest_arena_indicators

class ArenaHistoryMock:
    def __init__(self, player_id, category, arena_number, rank_position, win_count, kill_value, recorded_at):
        self.player_id = player_id
        self.category = category
        self.arena_number = arena_number
        self.rank_position = rank_position
        self.win_count = win_count
        self.kill_value = kill_value
        self.recorded_at = recorded_at

class TestArenaIndicators(unittest.TestCase):
    def test_champion_multiple_records(self):
        # Três registros, compara os dois mais recentes
        latest = ArenaHistoryMock(1, 'champion', 3, 1, 12, 110, '2026-03-17 23:30')
        previous = ArenaHistoryMock(1, 'champion', 2, 2, 10, 100, '2026-03-16 23:30')
        older = ArenaHistoryMock(1, 'champion', 1, 3, 8, 90, '2026-03-15 23:30')
        self.session.query().filter().order_by().limit().all.return_value = [latest, previous, older]
        indicators = get_latest_arena_indicators(self.session, 1, 'champion')
        self.assertEqual(indicators['win_change'], 2)
        self.assertEqual(indicators['kill_change'], 10)
        self.assertTrue(indicators['win_active'])
        self.assertTrue(indicators['kill_active'])

    def test_aspirant_multiple_records(self):
        # Três registros, compara os dois mais recentes
        latest = ArenaHistoryMock(2, 'aspirant', 3, 1, 9, 60, '2026-03-17 23:30')
        previous = ArenaHistoryMock(2, 'aspirant', 2, 2, 7, 55, '2026-03-16 23:30')
        older = ArenaHistoryMock(2, 'aspirant', 1, 3, 5, 50, '2026-03-15 23:30')
        self.session.query().filter().order_by().limit().all.return_value = [latest, previous, older]
        indicators = get_latest_arena_indicators(self.session, 2, 'aspirant')
        self.assertEqual(indicators['win_change'], 2)
        self.assertEqual(indicators['kill_change'], 5)
        self.assertTrue(indicators['win_active'])
        self.assertTrue(indicators['kill_active'])
        
    def setUp(self):
        self.session = MagicMock()

    def test_indicators_with_two_records(self):
        # Simula dois registros para o mesmo player e categoria
        latest = ArenaHistoryMock(1, 'champion', 2, 1, 10, 100, '2026-03-16 23:30')
        previous = ArenaHistoryMock(1, 'champion', 1, 2, 5, 90, '2026-03-15 23:30')
        self.session.query().filter().order_by().limit().all.return_value = [latest, previous]
        indicators = get_latest_arena_indicators(self.session, 1, 'champion')
        self.assertEqual(indicators['win_change'], 5)
        self.assertEqual(indicators['kill_change'], 10)
        self.assertTrue(indicators['win_active'])
        self.assertTrue(indicators['kill_active'])

    def test_indicators_with_one_record(self):
        # Apenas um registro, não deve exibir indicador
        latest = ArenaHistoryMock(1, 'champion', 2, 1, 10, 100, '2026-03-16 23:30')
        self.session.query().filter().order_by().limit().all.return_value = [latest]
        indicators = get_latest_arena_indicators(self.session, 1, 'champion')
        self.assertEqual(indicators['win_change'], 0)
        self.assertFalse(indicators['win_active'])

    def test_indicators_with_different_category(self):
        # Categoria diferente, não deve exibir indicador
        latest = ArenaHistoryMock(1, 'aspirant', 2, 1, 10, 100, '2026-03-16 23:30')
        previous = ArenaHistoryMock(1, 'aspirant', 1, 2, 5, 90, '2026-03-15 23:30')
        self.session.query().filter().order_by().limit().all.return_value = [latest, previous]
        indicators = get_latest_arena_indicators(self.session, 1, 'champion')
        self.assertEqual(indicators['win_change'], 0)
        self.assertFalse(indicators['win_active'])

if __name__ == '__main__':
    unittest.main()
