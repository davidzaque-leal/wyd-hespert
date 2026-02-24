from app.database import SessionLocal
from app.repositories.level_repository import LevelRepository

session = SessionLocal()
players = LevelRepository.get_all(session)
session.close()

print('=== Verificando se os nomes das linhagens estao sendo retornados ===\n')
for i, p in enumerate(players[:3]):
    print(f'Player {i+1}: {p.player.name}')
    print(f'  Celestial Lineage Name: {p.celestial_lineage_name}')
    print(f'  Subclass Lineage Name: {p.subclass_lineage_name}')
    print()
