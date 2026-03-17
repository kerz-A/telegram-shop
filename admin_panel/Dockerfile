FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY admin_panel/requirements.txt /app/admin_panel/requirements.txt
RUN pip install --no-cache-dir -r /app/admin_panel/requirements.txt

COPY shop_core /app/shop_core
RUN pip install --no-cache-dir -e /app/shop_core

COPY admin_panel /app/admin_panel

ENV DJANGO_SETTINGS_MODULE=config.settings

EXPOSE 8000
