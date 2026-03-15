from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from app.models import LevelRanking, Player, ClassLineage

class LevelRepository:

    @staticmethod
    def clear(session: Session):
        session.query(LevelRanking).delete(synchronize_session=False)

    @staticmethod
    def save(session: Session, player, ranking_data):
        # Get celestial lineage name
        celestial_lineage_name = ranking_data.get("celestial_lineage")
        if celestial_lineage_name is None and player.class_id is not None and player.class_lineage is not None:
            cel_lineage = session.query(ClassLineage).filter(
                ClassLineage.class_id == player.class_id,
                ClassLineage.lineage_index == player.class_lineage
            ).first()
            if cel_lineage:
                celestial_lineage_name = cel_lineage.name

        # Get subclass lineage name
        subclass_lineage_name = ranking_data.get("subclass_lineage")
        if subclass_lineage_name is None and player.subclass is not None and player.subclass_lineage is not None:
            sub_lineage = session.query(ClassLineage).filter(
                ClassLineage.class_id == player.subclass,
                ClassLineage.lineage_index == player.subclass_lineage
            ).first()
            if sub_lineage:
                subclass_lineage_name = sub_lineage.name
        
        from app.services.ranking_history_service import get_formatted_now
        snapshot_date = get_formatted_now()
        ranking = LevelRanking(
            player_id=player.id,
            points=ranking_data.get("points"),
            level_celestial=ranking_data.get("level"),
            celestial_lineage_name=celestial_lineage_name,
            level_sub_celestial=ranking_data.get("levelSub"),
            subclass_lineage_name=subclass_lineage_name,
            level_total=ranking_data.get("Soma Level"),
            snapshot_date=snapshot_date
        )
        session.add(ranking)
        return snapshot_date  # Para sincronizar com histórico

    @staticmethod
    def get_all(session: Session):
        rankings = (
            session.query(LevelRanking)
            .options(joinedload(LevelRanking.player).joinedload(Player.guild))
            .order_by(LevelRanking.level_total.desc())
            .all()
        )
        
        # Enrich rankings with lineage names from class_lineages table
        for ranking in rankings:
            player = ranking.player
            
            # Get celestial lineage name
            if not ranking.celestial_lineage_name and player.class_id is not None and player.class_lineage is not None:
                cel_lineage = session.query(ClassLineage).filter(
                    ClassLineage.class_id == player.class_id,
                    ClassLineage.lineage_index == player.class_lineage
                ).first()
                if cel_lineage:
                    ranking.celestial_lineage_name = cel_lineage.name
            
            # Get subclass lineage name
            if not ranking.subclass_lineage_name and player.subclass is not None and player.subclass_lineage is not None:
                sub_lineage = session.query(ClassLineage).filter(
                    ClassLineage.class_id == player.subclass,
                    ClassLineage.lineage_index == player.subclass_lineage
                ).first()
                if sub_lineage:
                    ranking.subclass_lineage_name = sub_lineage.name
        
        return rankings