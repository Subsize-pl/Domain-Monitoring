FROM python:3.13.5-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/src

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY alembic.ini ./

RUN uv pip install --system .

RUN chmod +x /app/scripts/prestart.sh

EXPOSE 8000

ENTRYPOINT ["/app/scripts/prestart.sh"]