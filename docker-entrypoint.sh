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

echo "📦 Running migrations for public schema..."
uv run python manage.py migrate_schemas --shared

echo "🏢 Setting up development tenants..."
uv run python manage.py setup_dev_tenants

echo "📦 Running migrations for tenant schemas..."
uv run python manage.py migrate_schemas --tenant || true

echo "📁 Collecting static files..."
uv run python manage.py collectstatic --noinput || true

echo "🚀 Starting server..."
exec "$@"