#!/bin/sh
set -eu

echo "Running migrations..."
python -m alembic upgrade head

echo "Starting app..."
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000