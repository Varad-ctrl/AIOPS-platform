#!/usr/bin/env bash
set -e

echo "Waiting for database..."
until python -c "
import sys, time
from sqlalchemy import create_engine, text
from app.core.config import settings
for i in range(30):
    try:
        create_engine(settings.DATABASE_URL).connect().close()
        sys.exit(0)
    except Exception:
        time.sleep(1)
sys.exit(1)
"; do
  echo "Database not ready yet, retrying..."
  sleep 1
done

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
