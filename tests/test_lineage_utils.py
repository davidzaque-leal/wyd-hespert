import pytest
from unittest.mock import MagicMock
from app.utils.lineage_utils import LineageUtils

@pytest.fixture
def mock_session():
    session = MagicMock()
    return session

@pytest.fixture
def mock_player():
    player = MagicMock()
    player.class_id = 1
    player.class_lineage = 2
    player.subclass = 3
    player.subclass_lineage = 4
    return player

def test_get_celestial_lineage_name_found(mock_session, mock_player):
    lineage = MagicMock()
    lineage.name = "Celestial"
    mock_session.query().filter().first.return_value = lineage
    name = LineageUtils.get_celestial_lineage_name(mock_session, mock_player)
    assert name == "Celestial"

def test_get_celestial_lineage_name_not_found(mock_session, mock_player):
    mock_session.query().filter().first.return_value = None
    name = LineageUtils.get_celestial_lineage_name(mock_session, mock_player)
    assert name is None

def test_get_subclass_lineage_name_found(mock_session, mock_player):
    lineage = MagicMock()
    lineage.name = "SubClass"
    mock_session.query().filter().first.return_value = lineage
    name = LineageUtils.get_subclass_lineage_name(mock_session, mock_player)
    assert name == "SubClass"

def test_get_subclass_lineage_name_not_found(mock_session, mock_player):
    mock_session.query().filter().first.return_value = None
    name = LineageUtils.get_subclass_lineage_name(mock_session, mock_player)
    assert name is None

def test_get_all_lineages(mock_session, mock_player):
    # Simula ambos retornando nomes
    cel_mock = MagicMock()
    cel_mock.name = "Celestial"
    sub_mock = MagicMock()
    sub_mock.name = "SubClass"
    mock_session.query().filter().first.side_effect = [cel_mock, sub_mock]
    result = LineageUtils.get_all_lineages(mock_session, mock_player)
    assert result["celestial"] == "Celestial"
    assert result["subclass"] == "SubClass"
