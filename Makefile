.PHONY: up down logs build server-local clean

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f mcp-server

db-shell:
	docker compose exec business-db psql -U readonly -d business

server-local:
	cd server && uv run alembic upgrade head && uv run python -m src.server

clean:
	docker compose down -v
