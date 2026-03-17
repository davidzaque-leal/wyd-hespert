import pytest
from app.services.hash_manager import HashManager
from app.database import SessionLocal
from app.models import SyncHash

def test_calc_hash_consistency():
    data1 = {"a": 1, "b": 2}
    data2 = {"b": 2, "a": 1}  # Ordem diferente
    hash1 = HashManager._calc_hash(data1)
    hash2 = HashManager._calc_hash(data2)
    assert hash1 == hash2

def test_check_and_update_hash_db():
    session = SessionLocal()
    # Limpa SyncHash para o teste
    session.query(SyncHash).filter(SyncHash.name == "pytest").delete()
    session.commit()
    data = {"x": 10}
    changed = HashManager.check_and_update_hash("pytest", data)
    assert changed is True
    changed = HashManager.check_and_update_hash("pytest", data)
    assert changed is False
    changed = HashManager.check_and_update_hash("pytest", {"x": 11})
    assert changed is True
    # Verifica persistência
    hash_row = session.query(SyncHash).filter_by(name="pytest").first()
    assert hash_row is not None
    assert hash_row.hash_value == HashManager._calc_hash({"x": 11})
    session.close()
