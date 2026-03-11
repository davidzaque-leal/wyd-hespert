import pytest
from unittest.mock import MagicMock, patch
from app.services.player_serializer import PlayerSerializer

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def mock_player():
    player = MagicMock()
    player.name = "Player1"
    player.guild = MagicMock()
    player.guild.external_id = "GuildX"
    return player

def test_serialize_level_ranking(mock_session, mock_player):
    ranking = MagicMock()
    ranking.player = mock_player
    ranking.level_celestial = 10
    ranking.celestial_lineage_name = "Celestial"
    ranking.level_subclass = 5
    ranking.subclass_lineage_name = "SubClass"
    ranking.level_total = 15
    with patch('app.utils.lineage_utils.LineageUtils.get_all_lineages', return_value={"celestial": "Celestial", "subclass": "SubClass"}):
        result = PlayerSerializer.serialize_level_ranking(ranking, mock_session)
        assert result["name"] == "Player1"
        assert result["celestial_lineage"] == "Celestial"
        assert result["subclass_lineage"] == "SubClass"
        assert result["guild"] == "GuildX"

def test_serialize_arena_ranking():
    ranking = MagicMock()
    ranking.player.name = "Player1"
    ranking.win_count = 3
    ranking.kill_value = 5
    ranking.death_value = 1
    ranking.total = 9
    result = PlayerSerializer.serialize_arena_ranking(ranking)
    assert result["charName"] == "Player1"
    assert result["winCount"] == 3
    assert result["killValue"] == 5
    assert result["deathValue"] == 1
    assert result["total"] == 9

def test_serialize_player_search(mock_session, mock_player):
    with patch('app.utils.lineage_utils.LineageUtils.get_all_lineages', return_value={"celestial": "Celestial", "subclass": "SubClass"}):
        result = PlayerSerializer.serialize_player_search(mock_player, mock_session, rank_position=2)
        assert result["name"] == "Player1"
        assert result["guild"] == "GuildX"
        assert result["celestial_lineage"] == "Celestial"
        assert result["subclass_lineage"] == "SubClass"
        assert result["rank_position"] == 2
