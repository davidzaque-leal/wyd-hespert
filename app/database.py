from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import logging

# Default to the Postgres DB you provided; allow override via env var
DEFAULT_PG = "postgresql+psycopg://postgres:kiko3284@localhost:5432/wyd"
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_PG)


def _make_engine(url: str):
	if url.startswith("sqlite"):
		connect_args = {"check_same_thread": False}
		return create_engine(url, echo=False, connect_args=connect_args)
	# for Postgres (psycopg) set a short connect timeout so failures are quick
	return create_engine(url, echo=False, connect_args={"connect_timeout": 3})


# Try to create an engine and test a quick connection. If Postgres isn't
# available (common in local dev), fall back to a local SQLite file so the
# app can still start and be used without a running Postgres instance.
try:
	engine = _make_engine(DATABASE_URL)
	with engine.connect():
		pass
except Exception as e:
	logging.warning("Failed to connect to DB at %s: %s. Falling back to SQLite.", DATABASE_URL, e)
	sqlite_url = os.environ.get("DEV_DATABASE_URL", "sqlite:///./wyd_dev.db")
	engine = _make_engine(sqlite_url)
	DATABASE_URL = sqlite_url

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()