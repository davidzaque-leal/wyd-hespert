from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import logging

# Apenas Postgres como banco de dados
DEFAULT_PG = "postgresql+psycopg://postgres:kiko3284@localhost:5432/wyd"
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_PG)

def _make_engine(url: str):
	# Apenas Postgres
	return create_engine(url, echo=False, connect_args={"connect_timeout": 3})

engine = _make_engine(DATABASE_URL)
with engine.connect():
	pass

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()