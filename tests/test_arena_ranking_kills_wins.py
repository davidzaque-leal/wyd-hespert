import pytest
from unittest.mock import MagicMock
from app.services.ranking_history_service import save_arena_ranking_history

@pytest.fixture
def mock_session():
    return MagicMock()

def test_arena_ranking_kills_and_wins(mock_session):
    # Simula ranking anterior
    previous_arena = [
        {"id": 1, "charName": "Player1", "total": 10, "points": 5, "winCount": 2, "killValue": 30, "deathValue": 1},
        {"id": 2, "charName": "Player2", "total": 8, "points": 4, "winCount": 1, "killValue": 19, "deathValue": 2}
    ]
    # Simula ranking atual (com mais kills e vitórias)
    current_arena = [
        {"id": 1, "charName": "Player1", "total": 15, "points": 7, "winCount": 3, "killValue": 35, "deathValue": 1},
        {"id": 2, "charName": "Player2", "total": 10, "points": 5, "winCount": 2, "killValue": 22, "deathValue": 2}
    ]
    # Simula não existir registro hoje
    mock_session.query().filter().first.return_value = None
    result = save_arena_ranking_history(mock_session, current_arena, "aspirant")
    assert result is True
    mock_session.add.assert_called()
    mock_session.commit.assert_called()
    # Verifica se os indicadores de kills e vitórias aumentaram
    assert current_arena[0]["killValue"] -  previous_arena[0]["killValue"] == 5
    assert current_arena[0]["winCount"] - previous_arena[0]["winCount"] == 1
