.PHONY: Makefile
help:
	@echo "Read the Makefile plz"

autoformat/black:
	poetry run black plugin_store/ tests/

autoformat/isort:
	poetry run isort plugin_store/ tests/

autoformat: autoformat/black autoformat/isort

lint/flake8:
	poetry run flake8 plugin_store/ tests/

lint/isort:
	poetry run isort --check --diff plugin_store/ tests/

lint/black:
	poetry run black --check --diff plugin_store/ tests/

lint/mypy:
	PYTHON_PATH=./plugin_store poetry run mypy plugin_store/ tests/

lint: lint/black lint/isort lint/flake8 lint/mypy

migrations/apply:
	poetry run alembic upgrade head

migrations/autogenerate:
	poetry run alembic revision --autogenerate

migrations/create:
	poetry run alembic revision

dc/build:
	docker compose -f docker-compose.local.yml build

dc/%:
	docker compose -f docker-compose.local.yml run -w /app plugin_store make $*

deps/lock:
	poetry lock --no-update

deps/upgrade:
	poetry lock

test:
	SQLALCHEMY_WARN_20=1 poetry run pytest ./tests