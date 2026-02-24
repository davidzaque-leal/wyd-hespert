import threading
import time
import json
import os
from app.services.api import get_level_ranking, get_arena_ranking
from app.services.sync_service import SyncService
from app.database import SessionLocal
from app.models import LevelRanking, ArenaRanking, Player
from app.repositories.level_repository import LevelRepository
from app.services.player_serializer import PlayerSerializer




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

    # ===============================
    # Atualização dos dados da API
    # ===============================
    def update_data(self):
        try:
            print("🔄 Sincronizando e atualizando dados no banco...")

            # Use SyncService to fetch and persist data into the DB
            SyncService.sync_all()

            # Load normalized structures from DB for templates
            session = SessionLocal()
            try:
                # Use LevelRepository to get enriched rankings with lineage names
                level_rows = LevelRepository.get_all(session)

                champion_rows = (
                    session.query(ArenaRanking).join(Player).filter(ArenaRanking.category == "champion").order_by(ArenaRanking.total.desc()).all()
                )

                aspirant_rows = (
                    session.query(ArenaRanking).join(Player).filter(ArenaRanking.category == "aspirant").order_by(ArenaRanking.total.desc()).all()
                )

                with self.lock:
                    # Build lists using PlayerSerializer - Centralizado
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

                    self.last_update = time.strftime("%Y-%m-%d %H:%M:%S")

                self._save_backup()

                print("✅ Dados sincronizados e carregados do banco com sucesso!")
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