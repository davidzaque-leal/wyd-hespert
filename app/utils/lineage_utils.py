"""
Utilitários para buscar e formatar informações de linhagens
Centraliza a lógica de busca de linhagens para evitar redundâncias
"""
from sqlalchemy.orm import Session
from app.models import ClassLineage


class LineageUtils:
    """Classe utilitária para operações com linhagens"""
    
    @staticmethod
    def get_celestial_lineage_name(session: Session, player) -> str:
        """
        Obtém o nome da linhagem celestial de um player
        
        Args:
            session: SQLAlchemy session
            player: Objeto Player ou LevelRanking
            
        Returns:
            Nome da linhagem ou None se não encontrada
        """
        if not hasattr(player, 'class_id') or not hasattr(player, 'class_lineage'):
            return None
            
        if player.class_id is None or player.class_lineage is None:
            return None
        
        lineage = session.query(ClassLineage).filter(
            ClassLineage.class_id == player.class_id,
            ClassLineage.lineage_index == player.class_lineage
        ).first()
        
        return lineage.name if lineage else None
    
    @staticmethod
    def get_subclass_lineage_name(session: Session, player) -> str:
        """
        Obtém o nome da linhagem sub de um player
        
        Args:
            session: SQLAlchemy session
            player: Objeto Player ou LevelRanking
            
        Returns:
            Nome da linhagem ou None se não encontrada
        """
        if not hasattr(player, 'subclass') or not hasattr(player, 'subclass_lineage'):
            return None
            
        if player.subclass is None or player.subclass_lineage is None:
            return None
        
        lineage = session.query(ClassLineage).filter(
            ClassLineage.class_id == player.subclass,
            ClassLineage.lineage_index == player.subclass_lineage
        ).first()
        
        return lineage.name if lineage else None
    
    @staticmethod
    def get_all_lineages(session: Session, player) -> dict:
        """
        Obtém ambas as linhagens de um player
        
        Args:
            session: SQLAlchemy session
            player: Objeto Player
            
        Returns:
            Dicionário com 'celestial' e 'subclass'
        """
        return {
            "celestial": LineageUtils.get_celestial_lineage_name(session, player),
            "subclass": LineageUtils.get_subclass_lineage_name(session, player),
        }
