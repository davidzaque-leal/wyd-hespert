import pytest
from sqlalchemy.orm import Session
from app.repositories.player_repository import PlayerRepository
from app.models import Player
from app.database import SessionLocal

@pytest.fixture
def session():
    s = SessionLocal()
    yield s
    s.close()

# Testa se SQL injection é bloqueado na busca por nome
@pytest.mark.parametrize("malicious_input", [
    "' OR 1=1 --",
    '" OR "a"="a',
    "1; DROP TABLE players; --",
    "admin' --",
    "'; EXEC xp_cmdshell('dir'); --"
])
def test_sql_injection_get_by_name(session, malicious_input):
    result = PlayerRepository.get_by_name(session, malicious_input)
    # Não deve retornar nenhum player, nem causar erro
    assert result is None

# Testa se SQL injection é bloqueado na busca por linhagem
@pytest.mark.parametrize("malicious_input", [
    "' OR 1=1 --",
    '" OR "a"="a',
    "1; DROP TABLE players; --",
    "admin' --",
    "'; EXEC xp_cmdshell('dir'); --"
])
def test_sql_injection_get_by_lineage(session, malicious_input):
    result = PlayerRepository.get_by_lineage(session, malicious_input)
    # Não deve retornar players, nem causar erro
    assert isinstance(result, list)
    assert len(result) == 0
