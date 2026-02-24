"""
Serializador de dados de players para padronizar a estrutura de dados em templates
"""
from sqlalchemy.orm import Session
from app.utils.lineage_utils import LineageUtils


class PlayerSerializer:
    """Serializa dados de players para uso em templates"""
    
    @staticmethod
    def serialize_level_ranking(ranking, session: Session) -> dict:
        """
        Serializa dados de LevelRanking
        
        Args:
            ranking: Objeto LevelRanking
            session: SQLAlchemy session
            
        Returns:
            Dicionário padronizado com dados do ranking
        """
        lineages = LineageUtils.get_all_lineages(session, ranking.player)
        
        return {
            "name": ranking.player.name,
            "level": ranking.level_celestial,
            "celestial_lineage": ranking.celestial_lineage_name or lineages.get("celestial"),
            "levelSub": ranking.level_subclass,
            "subclass_lineage": ranking.subclass_lineage_name or lineages.get("subclass"),
            "Soma Level": ranking.level_total,
            "guild": ranking.player.guild.external_id if ranking.player.guild else None,
        }
    
    @staticmethod
    def serialize_arena_ranking(ranking) -> dict:
        """
        Serializa dados de ArenaRanking
        
        Args:
            ranking: Objeto ArenaRanking
            
        Returns:
            Dicionário padronizado com dados da arena
        """
        return {
            "charName": ranking.player.name,
            "winCount": ranking.win_count,
            "killValue": ranking.kill_value,
            "deathValue": ranking.death_value,
            "total": ranking.total,
        }
    
    @staticmethod
    def serialize_player_search(player, session: Session) -> dict:
        """
        Serializa dados de um Player para a página de busca
        
        Args:
            player: Objeto Player
            session: SQLAlchemy session
            
        Returns:
            Dicionário padronizado com dados do player
        """
        lineages = LineageUtils.get_all_lineages(session, player)
        
        return {
            "name": player.name,
            "guild_external_id": player.guild.external_id if player.guild else None,
            "celestial_lineage": lineages.get("celestial"),
            "subclass_lineage": lineages.get("subclass"),
        }
