FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV PYTHONPATH=/app

COPY pyproject.toml ./
RUN uv sync --no-cache --no-install-project

COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY src/ ./src/

EXPOSE 8000

CMD ["sh", "-c", "uv run alembic upgrade head && uv run python -m src.server"]
