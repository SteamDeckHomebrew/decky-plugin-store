FROM python:alpine3.7

RUN apk add build-base
RUN apk add openssl-dev
RUN apk add python3-dev

COPY ./requirements.txt /
RUN pip install -r /requirements.txt

COPY ./plugin_store /app
WORKDIR /app
ENV PYTHONUNBUFFERED=0

CMD python3 -u main.py