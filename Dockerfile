FROM python:3.11.1-alpine3.17

RUN apk add build-base
RUN apk add openssl-dev
RUN apk add python3-dev
RUN apk add curl libffi-dev  \
    && curl -sSL https://install.python-poetry.org | python - --version 1.3.1 \
    && apk del curl libffi-dev

ENV PATH="/root/.local/bin:$PATH"

COPY ./pyproject.toml ./poetry.lock /
RUN poetry install --no-interaction --no-root

COPY alembic.ini /
COPY ./plugin_store /app
WORKDIR /app
ENV PYTHONUNBUFFERED=0

ENTRYPOINT ["poetry", "run", "--"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5566"]