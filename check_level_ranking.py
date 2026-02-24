#!/usr/bin/env python
from app.database import SessionLocal
from sqlalchemy import text

session = SessionLocal()

# Verificar as novas colunas da tabela level_rankings
result = session.execute(text("""
    SELECT p.name, 
           lr.level_celestial, 
           lr.celestial_lineage_name,
           lr.level_subclass,
           lr.subclass_lineage_name,
           lr.level_total
    FROM level_rankings lr
    JOIN players p ON p.id = lr.player_id
    LIMIT 15
"""))

print("Level Rankings - New Columns:")
print("="*110)
for row in result:
    name, level_cel, cel_lineage, level_sub, sub_lineage, level_total = row
    print(f"{name:20} | Cel: {level_cel:3} | {cel_lineage:20} | Sub: {level_sub:3} | {sub_lineage:20} | Total: {level_total}")

session.close()
