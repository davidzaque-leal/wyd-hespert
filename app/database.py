from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import logging
from app.utils.load_env import load_env

load_env()

import warnings
# Use apenas variáveis de ambiente para credenciais
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
	warnings.warn("DATABASE_URL não definida. Configure a variável de ambiente para conectar ao banco.")
	raise RuntimeError("DATABASE_URL não definida. Configure a variável de ambiente.")

def _make_engine(url: str):
	# Apenas Postgres
	return create_engine(url, echo=False, connect_args={"connect_timeout": 3})

engine = _make_engine(DATABASE_URL)
with engine.connect():
	pass

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()