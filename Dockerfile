FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    git gcc libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir setuptools

COPY evennia/ /app/evennia/
RUN pip install --no-cache-dir -e /app/evennia

COPY mygame/ /app/mygame/
WORKDIR /app/mygame

EXPOSE 4000 4001 4002

CMD ["evennia", "start", "-l"]
