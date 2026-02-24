from sqlalchemy import Column, Integer, String, SmallInteger, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


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

    kingdom = Column(String(20))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

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
    level_subclass = Column(Integer)  # Renamed from 'level_sub'
    subclass_lineage_name = Column(String(100))  # Name of subclass lineage
    level_total = Column(Integer)

    snapshot_date = Column(DateTime(timezone=True), server_default=func.now())

    player = relationship("Player", back_populates="level_rankings")


class ArenaRanking(Base):
    __tablename__ = "arena_rankings"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"))

    category = Column(String(20))
    register_count = Column(Integer)
    kill_value = Column(Integer)
    death_value = Column(Integer)
    win_count = Column(Integer)
    points = Column(Integer)
    bonus_kill = Column(Integer)
    total = Column(Integer)

    snapshot_date = Column(DateTime(timezone=True), server_default=func.now())

    player = relationship("Player", back_populates="arena_rankings")

    __table_args__ = (
        CheckConstraint("category IN ('champion','aspirant')"),
    )