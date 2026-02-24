#!/usr/bin/env python
from app.database import SessionLocal
from app.models import Player
from sqlalchemy import text

session = SessionLocal()

# Verificar campos class_lineage e subclass_lineage
result = session.execute(text("""
    SELECT id, name, class_id, class_lineage, subclass, subclass_lineage
    FROM players
    LIMIT 15
"""))

print("Players - Class Lineage and Subclass Lineage fields:")
print("="*90)
for row in result:
    pid, name, class_id, class_lin, subclass, subclass_lin = row
    print(f"ID: {pid:3} | Name: {name:20} | Class: {class_id} | ClassLin: {class_lin} | Sub: {subclass} | SubLin: {subclass_lin}")

session.close()
