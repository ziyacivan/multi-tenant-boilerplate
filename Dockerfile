FROM python:3.13-slim

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY . .

RUN mkdir -p staticfiles mediafiles

RUN mkdir -p /home/appuser/.cache/uv
RUN chown -R appuser:appuser /app /home/appuser

EXPOSE 8000

COPY docker-entrypoint.sh /docker-entrypoint.sh
COPY docker-entrypoint-celery.sh /docker-entrypoint-celery.sh
RUN chmod +x /docker-entrypoint.sh /docker-entrypoint-celery.sh

USER appuser

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]