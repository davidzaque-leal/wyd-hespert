#!/usr/bin/env python
from app.database import SessionLocal, Base, engine
from app.models import Player, LevelRanking, ArenaRanking, Guild
from app.services.sync_service import SyncService
from app.services.db_seed import seed_classes_and_lineages

# Drop and recreate tables
print("Recriando banco de dados...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Seed classes
seed_classes_and_lineages()

# Sync fresh
print("Sincronizando dados fresh...")
SyncService.sync_all()
print("Sync completo!\n")

# Verify player_id=1
session = SessionLocal()
player = session.query(Player).filter(Player.id == 1).first()
if player:
    print(f"Player ID: {player.id}")
    print(f"Player Name: {player.name}")
    print(f"Guild ID: {player.guild_id}")
    if player.guild:
        print(f"Guild External ID: {player.guild.external_id}")
    else:
        print("Guild: None")
    
    # Check level ranking
    lr = session.query(LevelRanking).filter(LevelRanking.player_id == 1).first()
    if lr:
        print(f"\nLevel Total: {lr.level_total}")
else:
    print("Player not found!")

session.close()
