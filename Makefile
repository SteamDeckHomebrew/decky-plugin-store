.PHONY: Makefile

.PHONY: help
help:
	@echo "Read the Makefile plz"

.PHONY: autoformat/black
autoformat/black:
	poetry run black plugin_store/ tests/

.PHONY: autoformat/isort
autoformat/isort:
	poetry run isort plugin_store/ tests/

.PHONY: autoformat
autoformat: autoformat/black autoformat/isort

.PHONY: lint/flake8
lint/flake8:
	poetry run flake8 plugin_store/ tests/

.PHONY: lint/isort
lint/isort:
	poetry run isort --check --diff plugin_store/ tests/

.PHONY: lint/black
lint/black:
	poetry run black --check --diff plugin_store/ tests/

.PHONY: lint/mypy
lint/mypy:
	PYTHON_PATH=./plugin_store poetry run mypy plugin_store/ tests/

.PHONY: lint
lint: lint/black lint/isort lint/flake8 lint/mypy

.PHONY: migrations/apply
migrations/apply:
	poetry run alembic upgrade head

.PHONY: migrations/autogenerate
migrations/autogenerate:
	poetry run alembic revision --autogenerate

.PHONY: migrations/create
migrations/create:
	poetry run alembic revision

.PHONY: dc/build
dc/build:
	docker compose -f docker-compose.local.yml build

.PHONY: dc/%
dc/%:
	docker compose -f docker-compose.local.yml run -w /app plugin_store make $*

.PHONY: deps/lock
deps/lock:
	poetry lock --no-update

.PHONY: deps/upgrade
deps/upgrade:
	poetry lock

.PHONY: test
test:
	SQLALCHEMY_WARN_20=1 poetry run pytest ./tests