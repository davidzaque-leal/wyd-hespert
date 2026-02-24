#!/usr/bin/env python
from app.database import SessionLocal
from app.models import Player, LevelRanking
from sqlalchemy import text

session = SessionLocal()

# Check top 10 players with their guilds
result = session.execute(text("""
    SELECT p.id, p.name, p.guild_id, g.external_id, lr.level_total
    FROM players p
    LEFT JOIN guilds g ON p.guild_id = g.id
    LEFT JOIN level_rankings lr ON p.id = lr.player_id
    ORDER BY lr.level_total DESC NULLS LAST
    LIMIT 10
"""))

print("Top 10 players with guilds:")
print("="*70)
for row in result:
    player_id, name, guild_id, external_id, level_total = row
    print(f"ID: {player_id:3} | Name: {name:20} | Guild ID: {guild_id:4} | Ext ID: {str(external_id):6} | Level: {level_total}")

session.close()
