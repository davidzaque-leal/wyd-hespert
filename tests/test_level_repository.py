import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.repositories.level_repository import LevelRepository
from app.models import Base, Player, ClassLineage, LevelRanking

@pytest.fixture(scope="module")
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def sample_player(test_db):
    test_db.query(Player).delete()
    player = Player(id=1, name="TestPlayer", class_id=1, subclass=2, class_lineage=1, subclass_lineage=2)
    test_db.add(player)
    test_db.commit()
    return player

@pytest.fixture
def sample_lineages(test_db):
    cel_lineage = ClassLineage(class_id=1, lineage_index=1, name="CelestialName")
    sub_lineage = ClassLineage(class_id=2, lineage_index=2, name="SubclassName")
    test_db.add_all([cel_lineage, sub_lineage])
    test_db.commit()
    return cel_lineage, sub_lineage

@pytest.fixture
def ranking_data():
    return {
        "points": 100,
        "level": 10,
        "levelSub": 5,
        "Soma Level": 15
    }

def test_clear(test_db):
    LevelRepository.clear(test_db)
    assert test_db.query(LevelRanking).count() == 0

def test_save(test_db, sample_player, sample_lineages, ranking_data):
    snapshot = LevelRepository.save(test_db, sample_player, ranking_data)
    test_db.commit()
    ranking = test_db.query(LevelRanking).first()
    assert ranking is not None
    assert ranking.player_id == sample_player.id
    assert ranking.celestial_lineage_name == "CelestialName"
    assert ranking.subclass_lineage_name == "SubclassName"
    assert ranking.level_total == ranking_data["Soma Level"]
    assert ranking.snapshot_date == snapshot

def test_get_all(test_db, sample_player, sample_lineages, ranking_data):
    test_db.query(LevelRanking).delete()
    LevelRepository.save(test_db, sample_player, ranking_data)
    test_db.commit()
    rankings = LevelRepository.get_all(test_db)
    assert len(rankings) == 1
    ranking = rankings[0]
    assert ranking.player.name == "TestPlayer"
    assert ranking.celestial_lineage_name == "CelestialName"
    assert ranking.subclass_lineage_name == "SubclassName"
    assert ranking.level_total == ranking_data["Soma Level"]
