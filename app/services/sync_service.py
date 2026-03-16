from app.services.hash_manager import HashManager
import requests
from sqlalchemy import text
from app.database import SessionLocal
from app.repositories.level_repository import LevelRepository
from app.repositories.arena_repository import ArenaRepository
from app.repositories.player_repository import PlayerRepository
from app.models import Guild

LEVEL_URL = "https://rn3xfhamppsetddkod6vwc24lu0lhcek.lambda-url.us-east-1.on.aws/component-rank"
ARENA_URL = "https://rn3xfhamppsetddkod6vwc24lu0lhcek.lambda-url.us-east-1.on.aws/royal-rank"

class SyncService:

    @staticmethod
    def sync_all():
        from datetime import datetime, timezone, timedelta
        session = SessionLocal()
        try:
            # LEVEL
            now = datetime.now(timezone(timedelta(hours=-3)))  # Brasília
            level_should_update = False
            # Check if it's 00:01 or if no snapshot exists for today
            from app.services.ranking_history_service import ensure_today_level_ranking_snapshot
            today_snapshot_exists = ensure_today_level_ranking_snapshot(session)
            if not today_snapshot_exists:
                level_should_update = True
            elif now.hour == 0 and now.minute == 1:
                level_should_update = True

            # ARENA CHAMPION
            champion_response = requests.get(f"{ARENA_URL}?category=champion")
            champion_data = champion_response.json()
            # ARENA ASPIRANT
            aspirant_response = requests.get(f"{ARENA_URL}?category=aspirant")
            aspirant_data = aspirant_response.json()

            # Só atualiza se algum hash mudou (apenas arena)
            champion_changed = HashManager.check_and_update_hash("champion", champion_data)
            aspirant_changed = HashManager.check_and_update_hash("aspirant", aspirant_data)

            # Arena só atualiza se hash mudar
            if not (champion_changed or aspirant_changed):
                print("SyncService: Nenhuma alteração detectada nos dados de arena, ignorando sync de arena.")

            # Level ranking só atualiza uma vez por dia
            if level_should_update:
                level_response = requests.post(LEVEL_URL, json={"options": {}})
                level_data = level_response.json()
                with session.begin():
                    LevelRepository.clear(session)
                    for player_data in level_data:
                        try:
                            pname = player_data.get("name") or player_data.get("charName")
                            pguild = player_data.get("guild")
                            print(f"Processing level entry: {pname!r}, guild={pguild}")
                        except Exception:
                            pass
                        player = PlayerRepository.get_or_create(session, player_data)
                        PlayerRepository.update_from_data(session, player, player_data)
                        LevelRepository.save(session, player, player_data)
                    session.flush()
                print("✓ Level ranking atualizado para o dia.")
            else:
                print("ℹ️ Level ranking já atualizado hoje, pulando.")

            # Arena update
            with session.begin():
                from app.models import ArenaCategoryEnum
                ArenaRepository.clear_category(session, ArenaCategoryEnum.champion)
                ArenaRepository.clear_category(session, ArenaCategoryEnum.aspirant)
                for arena_data in champion_data:
                    player = PlayerRepository.get_or_create(session, {"name": arena_data.get("charName")})
                    PlayerRepository.update_from_data(session, player, arena_data)
                    ArenaRepository.save(session, player, arena_data, ArenaCategoryEnum.champion)
                for arena_data in aspirant_data:
                    player = PlayerRepository.get_or_create(session, {"name": arena_data.get("charName")})
                    PlayerRepository.update_from_data(session, player, arena_data)
                    ArenaRepository.save(session, player, arena_data, ArenaCategoryEnum.aspirant)
                session.flush()
                try:
                    lvl_rows = session.execute(text("SELECT COUNT(*) FROM level_rankings")).scalar()
                except Exception:
                    lvl_rows = "n/a"
                try:
                    arena_rows = session.execute(text("SELECT COUNT(*) FROM arena_rankings")).scalar()
                except Exception:
                    arena_rows = "n/a"
                print(f"Sync debug: level_rankings={lvl_rows}, arena_rankings={arena_rows}")
            return True
        finally:
            session.close()