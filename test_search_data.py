#!/usr/bin/env python
from app.database import SessionLocal
from app.repositories.player_repository import PlayerRepository

session = SessionLocal()

# Test 1: Get all lineages
print("=" * 80)
print("TEST 1: All available lineages")
print("=" * 80)
lineages = PlayerRepository.get_all_lineages(session)
print(f"Total lineages: {len(lineages)}")
for lin in lineages[:10]:
    print(f"  - {lin['name']}")

# Test 2: Get all guilds
print("\n" + "=" * 80)
print("TEST 2: All guilds")
print("=" * 80)
guilds = PlayerRepository.get_all_guilds(session)
print(f"Total guilds: {len(guilds)}")
for guild in guilds:
    print(f"  - Guild ID {guild['id']} (Ext: {guild['external_id']}) - {guild['player_count']} players")

session.close()
