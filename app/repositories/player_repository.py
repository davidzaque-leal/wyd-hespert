from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timezone, timedelta
from app.models import Player, Guild, ClassLineage

# timezone de Brasília (GMT-3)
BRASILIA_TZ = timezone(timedelta(hours=-3))


class PlayerRepository:

    @staticmethod
    def _extract_name(player_data: dict):
        return player_data.get("name") or player_data.get("charName")

    @staticmethod
    def get_or_create(session: Session, player_data: dict):
        name = PlayerRepository._extract_name(player_data)
        player = session.query(Player).filter(Player.name == name).first()
        if player:
            # update existing record with any available fields
            PlayerRepository.update_from_data(session, player, player_data)
            return player

        # Create minimal player record and populate possible fields
        player = Player(name=name)
        # attach player to session before updating so relationships are tracked predictably
        session.add(player)
        PlayerRepository.update_from_data(session, player, player_data)
        session.flush()
        return player

    @staticmethod
    def get_by_name(session: Session, name: str):
        return session.query(Player).filter(Player.name == name).first()

    @staticmethod
    def get_by_lineage(session: Session, lineage_name: str):
        """
        Get all players with a specific lineage (by name).
        Searches both celestial class lineage and subclass lineage.
        
        Args:
            session: SQLAlchemy session
            lineage_name: Name of the lineage (e.g., "Magia Branca")
        
        Returns:
            List of Player objects matching the lineage
        """
        # Find all ClassLineage entries with the given name
        lineages = session.query(ClassLineage).filter(
            ClassLineage.name == lineage_name
        ).all()
        
        if not lineages:
            return []
        
        players = []
        for lineage in lineages:
            # Find players with this as celestial lineage
            celestial_players = session.query(Player).filter(
                Player.class_id == lineage.class_id,
                Player.class_lineage == lineage.lineage_index
            ).all()
            players.extend(celestial_players)
            
            # Find players with this as subclass lineage
            subclass_players = session.query(Player).filter(
                Player.subclass == lineage.class_id,
                Player.subclass_lineage == lineage.lineage_index
            ).all()
            players.extend(subclass_players)
        
        # Remove duplicates but preserve order
        seen = set()
        unique_players = []
        for player in players:
            if player.id not in seen:
                seen.add(player.id)
                unique_players.append(player)
        
        return unique_players

    @staticmethod
    def get_by_guild_id(session: Session, guild_id: int):
        """
        Get all players from a specific guild.
        
        Args:
            session: SQLAlchemy session
            guild_id: Guild ID to filter by
        
        Returns:
            List of Player objects in the guild
        """
        return session.query(Player).filter(Player.guild_id == guild_id).all()

    @staticmethod
    def get_by_guild_and_lineage(session: Session, guild_id: int, lineage_name: str):
        """
        Get all players from a specific guild with a specific lineage.
        
        Args:
            session: SQLAlchemy session
            guild_id: Guild ID to filter by
            lineage_name: Name of the lineage (e.g., "Magia Branca")
        
        Returns:
            List of Player objects matching both conditions
        """
        # Find all ClassLineage entries with the given name
        lineages = session.query(ClassLineage).filter(
            ClassLineage.name == lineage_name
        ).all()
        
        if not lineages:
            return []
        
        players = []
        for lineage in lineages:
            # Find players in guild with this as celestial lineage
            celestial_players = session.query(Player).filter(
                Player.guild_id == guild_id,
                Player.class_id == lineage.class_id,
                Player.class_lineage == lineage.lineage_index
            ).all()
            players.extend(celestial_players)
            
            # Find players in guild with this as subclass lineage
            subclass_players = session.query(Player).filter(
                Player.guild_id == guild_id,
                Player.subclass == lineage.class_id,
                Player.subclass_lineage == lineage.lineage_index
            ).all()
            players.extend(subclass_players)
        
        # Remove duplicates but preserve order
        seen = set()
        unique_players = []
        for player in players:
            if player.id not in seen:
                seen.add(player.id)
                unique_players.append(player)
        
        return unique_players

    @staticmethod
    def update_from_data(session: Session, player: Player, data: dict):
        """
        Update player fields only from fields present in the payload.
        This preserves values from previous updates if a field is missing from current payload.
        Different routes provide different fields:
          - /component-rank: includes guild, class, subclass, kingdom, classLineage, etc
          - /royal-rank: does NOT include guild, class, subclass, classLineage, etc
        So we only update fields that are actually present in the payload.
        """
        updated = False

        # ===== GUILD =====
        # Only process if 'guild' field is in payload (from /component-rank)
        # /royal-rank does NOT send guild, so we preserve guild from previous sync
        if "guild" in data:
            external_id = None
            guild_value = data.get("guild")
            
            if guild_value is not None:
                try:
                    external_id = int(guild_value)
                except Exception:
                    pass
            
            # If guild is 0 or None, clear the association
            # Otherwise, find-or-create the guild and associate
            if external_id is not None and external_id != 0:
                guild = session.query(Guild).filter(Guild.external_id == external_id).first()
                if not guild:
                    guild = Guild(external_id=external_id)
                    session.add(guild)
                    session.flush()
                
                if player.guild_id != guild.id:
                    player.guild = guild
                    updated = True
            else:
                # guild is 0 or None or invalid - clear guild association
                if player.guild_id is not None:
                    player.guild = None
                    updated = True

        # ===== CLASS ID =====
        # Only update if ANY of these fields are present in payload
        if "class" in data or "classId" in data or "class_id" in data:
            class_id = data.get("classId") or data.get("class_id") or data.get("class")
            if class_id is not None:
                try:
                    new_class_id = int(class_id)
                    if player.class_id != new_class_id:
                        player.class_id = new_class_id
                        updated = True
                except Exception:
                    pass

        # ===== SUBCLASS =====
        # Only update if ANY of these fields are present in payload
        if "subclass" in data or "subClass" in data:
            subclass = data.get("subclass") or data.get("subClass")
            if subclass is not None:
                try:
                    new_subclass = int(subclass)
                    if player.subclass != new_subclass:
                        player.subclass = new_subclass
                        updated = True
                except Exception:
                    pass

        # ===== KINGDOM =====
        # Only update if 'kingdom' field is in payload
        if "kingdom" in data:
            kingdom = data.get("kingdom")
            if kingdom and player.kingdom != kingdom:
                player.kingdom = kingdom
                updated = True

        # ===== CLASS LINEAGE =====
        # Only update if 'classLineage' field is in payload (from /component-rank)
        if "classLineage" in data:
            class_lineage = data.get("classLineage")
            if class_lineage is not None:
                try:
                    new_class_lineage = int(class_lineage)
                    if player.class_lineage != new_class_lineage:
                        player.class_lineage = new_class_lineage
                        updated = True
                except Exception:
                    pass

        # ===== SUBCLASS LINEAGE =====
        # Only update if 'subClassLineage' field is in payload (from /component-rank)
        if "subClassLineage" in data:
            subclass_lineage = data.get("subClassLineage")
            if subclass_lineage is not None:
                try:
                    new_subclass_lineage = int(subclass_lineage)
                    if player.subclass_lineage != new_subclass_lineage:
                        player.subclass_lineage = new_subclass_lineage
                        updated = True
                except Exception:
                    pass

        # ===== TOUCHED TIMESTAMP =====
        if updated:
            from app.models import get_formatted_now
            player.updated_at = get_formatted_now()
            # ensure player is attached to session
            if player not in session:
                session.add(player)

    @staticmethod
    def get_all_lineages(session: Session):
        """
        Get all distinct lineage names available.
        
        Returns:
            List of dictionaries with lineage information sorted by name
        """
        lineages = session.query(ClassLineage).distinct(ClassLineage.name).order_by(ClassLineage.name).all()
        result = []
        seen = set()
        for lineage in session.query(ClassLineage).order_by(ClassLineage.name).all():
            if lineage.name not in seen:
                result.append({
                    "id": lineage.id,
                    "name": lineage.name,
                    "class_id": lineage.class_id
                })
                seen.add(lineage.name)
        return result

    @staticmethod
    def get_all_guilds(session: Session):
        """
        Get all guilds with players.
        
        Returns:
            List of dictionaries with guild information sorted by external_id
        """
        from sqlalchemy import func
        
        guilds_query = session.query(
            Guild.id,
            Guild.external_id,
            func.count(Player.id).label('player_count')
        ).outerjoin(Player).group_by(Guild.id, Guild.external_id).order_by(Guild.external_id).all()
        
        return [
            {
                "id": guild_id,
                "external_id": external_id,
                "player_count": player_count
            }
            for guild_id, external_id, player_count in guilds_query
        ]
