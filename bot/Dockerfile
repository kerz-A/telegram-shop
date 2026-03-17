FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY bot/requirements.txt /app/bot/requirements.txt
RUN pip install --no-cache-dir -r /app/bot/requirements.txt

COPY shop_core /app/shop_core
RUN pip install --no-cache-dir -e /app/shop_core

COPY bot /app/bot

RUN mkdir -p /app/bot/logs

CMD ["python", "-m", "bot.app.main"]
