#!/usr/bin/env python
from app.services.sync_service import SyncService
from app.database import SessionLocal
from app.models import Player
from app.services.db_seed import seed_classes_and_lineages

try:
    seed_classes_and_lineages()
except:
    pass

print("Sincronizando dados...")
SyncService.sync_all()

print("\nVerificando player_id=1:")
session = SessionLocal()
player = session.query(Player).filter(Player.id == 1).first()
if player:
    print(f"  Name: {player.name}")
    print(f"  Guild ID: {player.guild_id}")
    if player.guild:
        print(f"  Guild External ID: {player.guild.external_id}")
    else:
        print(f"  Guild: None")
else:
    print("  Player not found")
session.close()
