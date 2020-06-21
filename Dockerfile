FROM python:3.8.3-alpine3.11
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /
RUN apk add --no-cache --virtual .build-deps  \
    build-base \
    zlib-dev \
    postgresql-dev \
    git \
    && pip install --no-cache-dir -r /requirements.txt
COPY . /code
