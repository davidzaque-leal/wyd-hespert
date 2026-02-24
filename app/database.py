from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Default to the Postgres DB you provided; allow override via env var
DEFAULT_PG = "postgresql+psycopg://postgres:kiko3284@localhost:5432/wyd_fansite"
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_PG)

# For SQLite, need connect_args
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()