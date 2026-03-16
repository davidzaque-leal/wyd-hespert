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
    def check_hashes():
        """
        Checa os hashes das arenas e chama sync_all se algum hash mudou.
        """
        champion_response = requests.get(f"{ARENA_URL}?category=champion")
        champion_data = champion_response.json()
        aspirant_response = requests.get(f"{ARENA_URL}?category=aspirant")
        aspirant_data = aspirant_response.json()
        champion_changed = HashManager.check_and_update_hash("champion", champion_data)
        aspirant_changed = HashManager.check_and_update_hash("aspirant", aspirant_data)
        if champion_changed or aspirant_changed:
            SyncService.sync_all()
        else:
            print("SyncService: Nenhuma alteração detectada nos dados de arena, ignorando sync.")

    @staticmethod
    def sync_all():
        """
        Sincroniza rankings de level e arena.
        """
        SyncService.update_level()
        SyncService.update_arenas()
        return True

    @staticmethod
    def update_level():
        """
        Atualiza ranking de level se necessário.
        """
        from datetime import datetime, timezone, timedelta
        session = SessionLocal()
        try:
            now = datetime.now(timezone(timedelta(hours=-3)))  # Brasília
            level_should_update = False
            from app.services.ranking_history_service import ensure_today_level_ranking_snapshot
            today_snapshot_exists = ensure_today_level_ranking_snapshot(session)
            if not today_snapshot_exists:
                level_should_update = True
            elif now.hour == 0 and now.minute == 1:
                level_should_update = True
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
        finally:
            session.close()

    @staticmethod
    def update_arenas():
        """
        Atualiza ranking das arenas.
        """
        champion_response = requests.get(f"{ARENA_URL}?category=champion")
        champion_data = champion_response.json()
        aspirant_response = requests.get(f"{ARENA_URL}?category=aspirant")
        aspirant_data = aspirant_response.json()
        session = SessionLocal()
        try:
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
        finally:
            session.close()