#!/usr/bin/env bash
set -e

# Start script: cria tabelas e inicia uvicorn
PORT=${PORT:-8000}

echo "Running DB setup (create_tables.py)"
python create_tables.py || true

echo "Starting Uvicorn on 0.0.0.0:${PORT}"
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1
