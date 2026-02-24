import os
import sys
# Make sure project root is on sys.path so `app` package can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.database import SessionLocal

def inspect_db():
    session = SessionLocal()
    try:
        lvl = session.execute(text("SELECT COUNT(*) FROM level_rankings")).scalar()
        arena = session.execute(text("SELECT COUNT(*) FROM arena_rankings")).scalar()
        players = session.execute(text("SELECT COUNT(*) FROM players")).scalar()
        print(f"players={players}, level_rankings={lvl}, arena_rankings={arena}")

        print("\nSample players (first 10):")
        rows = session.execute(text("SELECT id, name, created_at FROM players ORDER BY id LIMIT 10")).fetchall()
        for r in rows:
            print(r)

        print("\nSample level ranking (first 10):")
        try:
            rows = session.execute(text("SELECT lr.id, p.name, lr.level_total, lr.level, lr.level_sub FROM level_rankings lr JOIN players p ON lr.player_id = p.id ORDER BY lr.level_total DESC LIMIT 10")).fetchall()
            for r in rows:
                print(r)
        except Exception as e:
            print("Could not query level_rankings:", e)

        print("\nSample arena ranking (first 10):")
        try:
            rows = session.execute(text("SELECT ar.id, p.name, ar.category, ar.total, ar.win_count FROM arena_rankings ar JOIN players p ON ar.player_id = p.id ORDER BY ar.total DESC LIMIT 10")).fetchall()
            for r in rows:
                print(r)
        except Exception as e:
            print("Could not query arena_rankings:", e)

    finally:
        session.close()

if __name__ == '__main__':
    inspect_db()
