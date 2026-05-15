#!/bin/sh
set -eu

echo "Running migrations..."
python -m alembic upgrade head

echo "Starting app..."
exec python -m domain_monitoring.main