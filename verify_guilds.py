#!/usr/bin/env python
from app.database import SessionLocal
from app.models import Player, LevelRanking
from sqlalchemy import text

session = SessionLocal()

# Players com guild=0 no level ranking (deveriam ter guild_id = NULL)
result = session.execute(text("""
    SELECT p.id, p.name, p.guild_id, lr.level_total
    FROM players p
    LEFT JOIN level_rankings lr ON p.id = lr.player_id
    WHERE p.guild_id IS NULL
    LIMIT 10
"""))

print("Players WITHOUT guild (guild_id is NULL):")
print("="*60)
for row in result:
    player_id, name, guild_id, level_total = row
    print(f"ID: {player_id:3} | Name: {name:20} | Guild ID: {guild_id}")

print("\n" + "="*60)

# Players com guild
result2 = session.execute(text("""
    SELECT p.id, p.name, p.guild_id, g.external_id, lr.level_total
    FROM players p
    LEFT JOIN guilds g ON p.guild_id = g.id
    LEFT JOIN level_rankings lr ON p.id = lr.player_id
    WHERE p.guild_id IS NOT NULL
    LIMIT 10
"""))

print("Players WITH guild:")
print("="*60)
for row in result2:
    player_id, name, guild_id, external_id, level_total = row
    print(f"ID: {player_id:3} | Name: {name:20} | Guild ID: {guild_id} | Ext ID: {external_id}")

session.close()
