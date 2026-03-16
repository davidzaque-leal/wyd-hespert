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
        session = SessionLocal()
        try:
            # LEVEL
            level_response = requests.post(LEVEL_URL, json={"options": {}})
            level_data = level_response.json()
            # ARENA CHAMPION
            champion_response = requests.get(f"{ARENA_URL}?category=champion")
            champion_data = champion_response.json()
            # ARENA ASPIRANT
            aspirant_response = requests.get(f"{ARENA_URL}?category=aspirant")
            aspirant_data = aspirant_response.json()

            # Só atualiza se algum hash mudou (apenas arena)
            champion_changed = HashManager.check_and_update_hash("champion", champion_data)
            aspirant_changed = HashManager.check_and_update_hash("aspirant", aspirant_data)

            # Ranking de level sempre atualiza uma vez por dia (agendado para 00:05)
            # Arena só atualiza se hash mudar
            if not (champion_changed or aspirant_changed):
                print("SyncService: Nenhuma alteração detectada nos dados de arena, ignorando sync de arena.")
            # Level sempre atualiza

            # run inside a transaction for safety
            with session.begin():
                # clear previous level and arena data, then insert fresh
                LevelRepository.clear(session)
                from app.models import ArenaCategoryEnum
                ArenaRepository.clear_category(session, ArenaCategoryEnum.champion)
                ArenaRepository.clear_category(session, ArenaCategoryEnum.aspirant)

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