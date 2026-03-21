import threading
import os
import time
import json
from app.database import SessionLocal
from app.repositories.level_repository import LevelRepository
from app.models import ArenaRanking, Player
from app.services.player_serializer import PlayerSerializer
from app.services.sync_service import SyncService
from app.services.ranking_history_service import save_level_ranking_history, save_arena_ranking_history

class DataStore:
    def __init__(self):
        self.level_ranking = []
        self.arena_champion = []
        self.arena_aspirant = []
        self.last_update = None
        self.lock = threading.Lock()
        self.backup_file = "data_backup.json"

        # Tenta restaurar backup ao iniciar
        self._load_backup()

    def update_data(self, sync: bool = True):
        try:
            updated = False
            if sync:
                print("🔄 Sincronizando e atualizando dados no banco...")
                updated = SyncService.sync_all()

            # Sempre carrega os dados atuais do banco
            session = SessionLocal()

            try:
                level_rows = LevelRepository.get_all(session)

                # Subquery para pegar o snapshot mais recente de cada player para cada categoria
                from sqlalchemy import func, and_
                subq_champion = (
                    session.query(
                        ArenaRanking.player_id,
                        func.max(ArenaRanking.snapshot_date).label("max_snapshot")
                    )
                    .filter(ArenaRanking.category == "champion")
                    .group_by(ArenaRanking.player_id)
                    .subquery()
                )
                champion_rows = (
                    session.query(ArenaRanking)
                    .join(subq_champion, and_(
                        ArenaRanking.player_id == subq_champion.c.player_id,
                        ArenaRanking.snapshot_date == subq_champion.c.max_snapshot
                    ))
                    .join(Player)
                    .filter(ArenaRanking.category == "champion")
                    .order_by(ArenaRanking.total.desc(), ArenaRanking.snapshot_date.desc())
                    .all()
                )

                subq_aspirant = (
                    session.query(
                        ArenaRanking.player_id,
                        func.max(ArenaRanking.snapshot_date).label("max_snapshot")
                    )
                    .filter(ArenaRanking.category == "aspirant")
                    .group_by(ArenaRanking.player_id)
                    .subquery()
                )
                aspirant_rows = (
                    session.query(ArenaRanking)
                    .join(subq_aspirant, and_(
                        ArenaRanking.player_id == subq_aspirant.c.player_id,
                        ArenaRanking.snapshot_date == subq_aspirant.c.max_snapshot
                    ))
                    .join(Player)
                    .filter(ArenaRanking.category == "aspirant")
                    .order_by(ArenaRanking.total.desc(), ArenaRanking.snapshot_date.desc())
                    .all()
                )

                with self.lock:
                    self.level_ranking = [
                        PlayerSerializer.serialize_level_ranking(lr, session)
                        for lr in level_rows
                    ]
                    self.arena_champion = [
                        PlayerSerializer.serialize_arena_ranking(a)
                        for a in champion_rows
                    ]
                    self.arena_aspirant = [
                        PlayerSerializer.serialize_arena_ranking(a)
                        for a in aspirant_rows
                    ]
                    if updated:
                        from app.utils.datetime_utils import get_formatted_now
                        self.last_update = get_formatted_now()

                if sync:
                    try:
                        save_level_ranking_history(session, self.level_ranking)
                        save_arena_ranking_history(session, self.arena_champion, "champion")
                        save_arena_ranking_history(session, self.arena_aspirant, "aspirant")
                    except Exception as e:
                        print(f"⚠ Erro ao salvar histórico de rankings: {e}")
                    self._save_backup()

                print("✅ Dados carregados do banco com sucesso!")
            finally:
                session.close()

        except Exception as e:
            print("❌ Erro ao atualizar API:", e)
            print("⚠ Mantendo dados anteriores (modo resiliente).")

    # ===============================
    # Ranking Combinado
    # ===============================
    def get_combined_ranking(self):
        with self.lock:
            arena_dict = {
                p["charName"]: p
                for p in self.arena_champion
            }

            combined = []

            for player in self.level_ranking:
                name = player["name"]
                arena_data = arena_dict.get(name)

                combined.append({
                    "name": name,
                    "level_total": player.get("Soma Level", 0),
                    "arena_points": arena_data.get("total", 0) if arena_data else 0,
                    "wins": arena_data.get("winCount", 0) if arena_data else 0,
                })

            return sorted(
                combined,
                key=lambda x: (x["arena_points"], x["level_total"]),
                reverse=True
            )

    # ===============================
    # Backup em JSON
    # ===============================
    def _save_backup(self):
        data = {
            "level_ranking": self.level_ranking,
            "arena_champion": self.arena_champion,
            "arena_aspirant": self.arena_aspirant,
            "last_update": self.last_update,
        }

        with open(self.backup_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_backup(self):
        if not os.path.exists(self.backup_file):
            return

        try:
            with open(self.backup_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.level_ranking = data.get("level_ranking", [])
            self.arena_champion = data.get("arena_champion", [])
            self.arena_aspirant = data.get("arena_aspirant", [])
            self.last_update = data.get("last_update")

            print("📦 Backup carregado com sucesso.")

        except Exception as e:
            print("⚠ Erro ao carregar backup:", e)


# Instância global
data_store = DataStore()