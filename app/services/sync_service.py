from app.services.hash_manager import HashManager
import requests
from sqlalchemy import text
from app.database import SessionLocal
from app.repositories.level_repository import LevelRepository
from app.repositories.arena_repository import ArenaRepository
from app.repositories.player_repository import PlayerRepository

from app.services.ranking_history_service import (
    save_level_ranking_history,
    save_arena_ranking_history,
    ensure_today_level_ranking_snapshot
)

LEVEL_URL = "https://rn3xfhamppsetddkod6vwc24lu0lhcek.lambda-url.us-east-1.on.aws/component-rank"
ARENA_URL = "https://rn3xfhamppsetddkod6vwc24lu0lhcek.lambda-url.us-east-1.on.aws/royal-rank"


class SyncService:

    @staticmethod
    def check_hashes():
        """
        Checa hashes das arenas e executa sync caso haja alteração.
        """
        try:
            champion_data = requests.get(f"{ARENA_URL}?category=champion").json()
            aspirant_data = requests.get(f"{ARENA_URL}?category=aspirant").json()

            champion_changed = HashManager.check_and_update_hash("champion", champion_data)
            aspirant_changed = HashManager.check_and_update_hash("aspirant", aspirant_data)

            if champion_changed or aspirant_changed:
                print("🔄 Alteração detectada nos rankings de arena. Sincronizando...")
                SyncService.sync_all()
            else:
                print("✓ Nenhuma alteração detectada nos rankings de arena.")

        except Exception as e:
            print(f"⚠ Erro ao verificar hashes: {e}")

    @staticmethod
    def sync_all():
        """
        Sincroniza todos os rankings.
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
            now = datetime.now(timezone(timedelta(hours=-3)))

            level_should_update = False
            today_snapshot_exists = ensure_today_level_ranking_snapshot(session)

            if not today_snapshot_exists:
                level_should_update = True
            elif now.hour == 0 and now.minute == 1:
                level_should_update = True

            if not level_should_update:
                print("ℹ️ Level ranking já atualizado hoje, pulando.")
                return

            print("🔄 Atualizando ranking de level...")

            level_data = requests.post(LEVEL_URL, json={"options": {}}).json()

            LevelRepository.clear(session)

            players_history = []

            for player_data in level_data:

                try:
                    pname = player_data.get("name") or player_data.get("charName")
                    pguild = player_data.get("guild")
                    print(f"Processing level entry: {pname} | guild={pguild}")
                except Exception:
                    pass

                player = PlayerRepository.get_or_create(session, player_data)
                PlayerRepository.update_from_data(session, player, player_data)

                LevelRepository.save(session, player, player_data)

                players_history.append({
                    "id": player.id,
                    "name": player.name,
                    "Soma Level": player_data.get("Soma Level"),
                    "points": player_data.get("points"),
                    "level": player_data.get("level"),
                    "levelSub": player_data.get("levelSub"),
                    "celestial_lineage": player_data.get("celestial_lineage"),
                    "subclass_lineage": player_data.get("subclass_lineage"),
                    "recorded_at": None
                })

            # salvar histórico
            save_level_ranking_history(session, players_history)

            session.commit()

            try:
                lvl_rows = session.execute(text("SELECT COUNT(*) FROM level_rankings")).scalar()
                print(f"✓ Level ranking atualizado. Total registros: {lvl_rows}")
            except Exception:
                pass

        except Exception as e:
            session.rollback()
            print(f"⚠ Erro ao atualizar ranking de level: {e}")

        finally:
            session.close()

    @staticmethod
    def update_arenas():
        """
        Atualiza ranking das arenas.
        """
        from app.models import ArenaCategoryEnum

        session = SessionLocal()

        try:
            print("🔄 Atualizando ranking de arenas...")

            champion_data = requests.get(f"{ARENA_URL}?category=champion").json()
            aspirant_data = requests.get(f"{ARENA_URL}?category=aspirant").json()

            ArenaRepository.clear_category(session, ArenaCategoryEnum.champion)
            ArenaRepository.clear_category(session, ArenaCategoryEnum.aspirant)

            champion_history = []
            aspirant_history = []

            for arena_data in champion_data:

                player = PlayerRepository.get_or_create(
                    session,
                    {"name": arena_data.get("charName")}
                )

                PlayerRepository.update_from_data(session, player, arena_data)

                ArenaRepository.save(
                    session,
                    player,
                    arena_data,
                    ArenaCategoryEnum.champion
                )

                history_data = arena_data.copy()
                history_data["id"] = player.id

                champion_history.append(history_data)

            for arena_data in aspirant_data:

                player = PlayerRepository.get_or_create(
                    session,
                    {"name": arena_data.get("charName")}
                )

                PlayerRepository.update_from_data(session, player, arena_data)

                ArenaRepository.save(
                    session,
                    player,
                    arena_data,
                    ArenaCategoryEnum.aspirant
                )

                history_data = arena_data.copy()
                history_data["id"] = player.id

                aspirant_history.append(history_data)

            # salvar histórico
            save_arena_ranking_history(session, champion_history, "champion")
            save_arena_ranking_history(session, aspirant_history, "aspirant")

            session.commit()

            try:
                lvl_rows = session.execute(text("SELECT COUNT(*) FROM level_rankings")).scalar()
                arena_rows = session.execute(text("SELECT COUNT(*) FROM arena_rankings")).scalar()

                print(f"✓ Arenas sincronizadas | level_rankings={lvl_rows} | arena_rankings={arena_rows}")

            except Exception:
                pass

        except Exception as e:
            session.rollback()
            print(f"⚠ Erro ao atualizar arenas: {e}")

        finally:
            session.close()