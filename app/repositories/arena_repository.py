from sqlalchemy.orm import Session
from app.models import ArenaRanking, Player, ArenaCategoryEnum
from app.utils.datetime_utils import get_formatted_now

class ArenaRepository:

    @staticmethod
    def clear_category(session: Session, category):
        if isinstance(category, str):
            category = ArenaCategoryEnum(category)
        session.query(ArenaRanking).filter(ArenaRanking.category == category).delete(synchronize_session=False)

    @staticmethod
    def save(session: Session, player: Player, arena_data: dict, category):
        if isinstance(category, str):
            category = ArenaCategoryEnum(category)
        snapshot_date = get_formatted_now()
        ranking = ArenaRanking(
            player_id=player.id,
            category=category,
            register_count=arena_data.get("registerCount") or arena_data.get("register_count"),
            kill_value=arena_data.get("killValue") or arena_data.get("kill_value"),
            death_value=arena_data.get("deathValue") or arena_data.get("death_value"),
            win_count=arena_data.get("winCount") or arena_data.get("win_count"),
            points=arena_data.get("points"),
            bonus_kill=arena_data.get("bonusKill") or arena_data.get("bonus_kill"),
            total=arena_data.get("total"),
            snapshot_date=snapshot_date
        )
        session.add(ranking)
        return snapshot_date  # Para sincronizar com histórico
