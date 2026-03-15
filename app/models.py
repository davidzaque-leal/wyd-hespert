from sqlalchemy import Column, Integer, String, SmallInteger, ForeignKey, CheckConstraint, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.database import Base

# Enums para campos
import enum

class ArenaCategoryEnum(enum.Enum):
    champion = "champion"
    aspirant = "aspirant"

class KingdomEnum(enum.Enum):
    blue = "blue"
    red = "red"
    none = "none"

class ArenaNumberEnum(enum.Enum):
    one = 1
    two = 2
    three = 3
    four = 4


def get_formatted_now():
    """
    Retorna a hora atual formatada como string 'DD/MM/YYYY HH:MM'.
    """
    now = datetime.now()
    return now.strftime('%d/%m/%Y %H:%M')


class Class(Base):
    __tablename__ = "classes"

    id = Column(SmallInteger, primary_key=True)
    name = Column(String(50), nullable=False)
    lineages = relationship("ClassLineage", back_populates="clazz")


class Guild(Base):
    __tablename__ = "guilds"

    id = Column(Integer, primary_key=True)
    # 'external_id' stores the numeric guild identifier (from API 'guild')
    external_id = Column(Integer, unique=True)


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    guild_id = Column(Integer, ForeignKey("guilds.id"))
    class_id = Column(SmallInteger, ForeignKey("classes.id"))

    subclass = Column(SmallInteger)
    class_lineage = Column(SmallInteger)
    subclass_lineage = Column(SmallInteger)

    kingdom = Column(Enum(KingdomEnum))

    created_at = Column(String(16), default=get_formatted_now)
    updated_at = Column(String(16), onupdate=get_formatted_now)

    guild = relationship("Guild")
    level_rankings = relationship("LevelRanking", back_populates="player")
    arena_rankings = relationship("ArenaRanking", back_populates="player")


class ClassLineage(Base):
    __tablename__ = "class_lineages"

    id = Column(Integer, primary_key=True)
    class_id = Column(SmallInteger, ForeignKey("classes.id", ondelete="CASCADE"))
    lineage_index = Column(SmallInteger)
    name = Column(String(100), nullable=False)

    clazz = relationship("Class", back_populates="lineages")


class LevelRanking(Base):
    __tablename__ = "level_rankings"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"))

    points = Column(Integer)
    level_celestial = Column(Integer)  # Renamed from 'level'
    celestial_lineage_name = Column(String(100))  # Name of celestial class lineage
    level_sub_celestial = Column(Integer)  # Renamed from 'level_sub'
    subclass_lineage_name = Column(String(100))  # Name of subclass lineage
    level_total = Column(Integer)

    snapshot_date = Column(String(16), default=get_formatted_now)

    player = relationship("Player", back_populates="level_rankings")


class ArenaRanking(Base):
    __tablename__ = "arena_rankings"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"))

    category = Column(Enum(ArenaCategoryEnum), nullable=False)
    register_count = Column(Integer)
    kill_value = Column(Integer)
    death_value = Column(Integer)
    win_count = Column(Integer)
    points = Column(Integer)
    bonus_kill = Column(Integer)
    total = Column(Integer)

    snapshot_date = Column(String(16), default=get_formatted_now)

    player = relationship("Player", back_populates="arena_rankings")

    __table_args__ = (
        CheckConstraint("category IN ('champion','aspirant')"),
    )


class LevelRankingHistory(Base):
    __tablename__ = "level_ranking_history"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"))
    player_name = Column(String(100), nullable=False)
    rank_position = Column(Integer)  # Posição no ranking
    level_total = Column(Integer)
    points = Column(Integer)
    level_celestial = Column(Integer)
    level_sub_celestial = Column(Integer)
    celestial_lineage_name = Column(String(100))
    subclass_lineage_name = Column(String(100))

    recorded_at = Column(String(16), default=get_formatted_now, index=True)

    player = relationship("Player", foreign_keys=[player_id])


class ArenaRankingHistory(Base):
    __tablename__ = "arena_ranking_history"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"))
    season = Column(String(5), nullable=False)  # MM/YY
    category = Column(Enum(ArenaCategoryEnum), nullable=False)  # champion ou aspirant
    arena_number = Column(Enum(ArenaNumberEnum), default=ArenaNumberEnum.one, nullable=False)  # 1, 2, 3, ou 4
    rank_position = Column(Integer)  # Posição no ranking
    total = Column(Integer)
    points = Column(Integer)
    win_count = Column(Integer)
    kill_value = Column(Integer)
    death_value = Column(Integer)

    recorded_at = Column(String(16), default=get_formatted_now, index=True)

    player = relationship("Player", foreign_keys=[player_id])

    __table_args__ = (
        CheckConstraint("category IN ('champion','aspirant')"),
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Integer, default=1)  # 1 = admin, 0 = não admin
    is_active = Column(Integer, default=1)  # 1 = ativo, 0 = desativado

    created_at = Column(String(16), default=get_formatted_now)
    updated_at = Column(String(16), onupdate=get_formatted_now)
