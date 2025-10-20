#!/bin/bash
set -e

echo "🔄 Waiting for PostgreSQL..."
while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
  sleep 1
done

echo "✅ PostgreSQL is ready!"

echo "🔄 Waiting for Redis..."
while ! redis-cli -h redis ping > /dev/null 2>&1; do
  sleep 1
done

echo "✅ Redis is ready!"

echo "🧹 Cleaning virtual environment..."
rm -rf .venv || true

echo "📦 Running migrations for public schema..."
uv run python manage.py migrate_schemas --shared

echo "📦 Running migrations for tenant schemas..."
uv run python manage.py migrate_schemas --tenant || true

echo "🚀 Starting Celery worker..."
exec "$@"