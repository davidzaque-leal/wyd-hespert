from app.database import SessionLocal
from app.repositories.level_repository import LevelRepository

session = SessionLocal()
players = LevelRepository.get_all(session)
session.close()

print('=== Primeiros 3 players no ranking ===')
for i, p in enumerate(players[:3]):
    print(f'\nPlayer {i+1}:')
    print(f'  Nome: {p.player.name}')
    print(f'  Linhagem Celestial: {p.celestial_lineage_name} (Nivel {p.level_celestial})')
    print(f'  Linhagem Sub: {p.subclass_lineage_name} (Nivel {p.level_subclass})')
    print(f'  Total: {p.level_total}')
    guild_id = p.player.guild.external_id if p.player.guild else 'Sem Guilda'
    print(f'  Guild: {guild_id}')

print('\n\nTemplates devem estar renderizando corretamente com os dados acima!')
