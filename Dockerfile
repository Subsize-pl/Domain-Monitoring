FROM python:3.13.5-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv && \
    uv pip install --system .

COPY src/ /app/
COPY scripts/ /app/scripts/
COPY alembic.ini /app/alembic.ini

RUN chmod +x /app/scripts/prestart.sh

EXPOSE 8000

ENTRYPOINT ["/app/scripts/prestart.sh"]