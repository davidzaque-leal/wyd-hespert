#!/usr/bin/env python
from app.database import SessionLocal
from app.repositories.player_repository import PlayerRepository

session = SessionLocal()

# Test 1: Get players by lineage
print("=" * 80)
print("TEST 1: Players with lineage 'Magia Branca'")
print("=" * 80)
players_by_lineage = PlayerRepository.get_by_lineage(session, "Magia Branca")
print(f"Total: {len(players_by_lineage)}")
for p in players_by_lineage[:10]:
    print(f"  - {p.name:20} | Class: {p.class_id} | Subclass: {p.subclass} | Guild: {p.guild_id}")

# Test 2: Get players by guild_id
print("\n" + "=" * 80)
print("TEST 2: Players in Guild ID 1 (External ID: 2300)")
print("=" * 80)
players_by_guild = PlayerRepository.get_by_guild_id(session, 1)
print(f"Total: {len(players_by_guild)}")
for p in players_by_guild[:10]:
    print(f"  - {p.name:20} | Class: {p.class_id} | Subclass: {p.subclass}")

# Test 3: Get players by guild AND lineage
print("\n" + "=" * 80)
print("TEST 3: Players in Guild ID 1 WITH lineage 'Magia Branca'")
print("=" * 80)
players_guild_lineage = PlayerRepository.get_by_guild_and_lineage(session, 1, "Magia Branca")
print(f"Total: {len(players_guild_lineage)}")
for p in players_guild_lineage:
    print(f"  - {p.name:20} | Class: {p.class_id} | Subclass: {p.subclass} | Guild: {p.guild_id}")

# Test 4: Try another combination
print("\n" + "=" * 80)
print("TEST 4: Players in Guild ID 3 (External ID: 2193) WITH lineage 'Natureza'")
print("=" * 80)
players_guild_lineage2 = PlayerRepository.get_by_guild_and_lineage(session, 3, "Natureza")
print(f"Total: {len(players_guild_lineage2)}")
for p in players_guild_lineage2:
    print(f"  - {p.name:20} | Class: {p.class_id} | Subclass: {p.subclass} | Guild: {p.guild_id}")

session.close()
