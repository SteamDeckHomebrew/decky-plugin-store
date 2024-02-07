FROM python:3.12.1-alpine3.19

ENV POETRY_INSTALLER_MAX_WORKERS=1
ENV POETRY_VIRTUALENVS_IN_PROJECT=false
ENV POETRY_VIRTUALENVS_PATH="/root/.venvs"
ENV VENV_PATH="${POETRY_VIRTUALENVS_PATH}/decky-plugin-store-9TtSrW0h-py3.12"

RUN apk add build-base
RUN apk add openssl-dev
RUN apk add python3-dev
RUN apk add curl libffi-dev  \
    && curl -sSL https://install.python-poetry.org | python - --version 1.7.1 \
    && apk del curl libffi-dev

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:/root/.local/bin:$PATH"

WORKDIR /app

COPY ./pyproject.toml ./poetry.lock /app/
RUN poetry install --no-interaction --no-root

# All directories are unpacked. Due to it, each file must be specified separately!
COPY ./alembic.ini ./LICENSE ./Makefile ./README.md /app/
COPY ./plugin_store/ /app/plugin_store
COPY ./tests/ /app/tests
WORKDIR /app/plugin_store
ENV PYTHONUNBUFFERED=0

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5566"]