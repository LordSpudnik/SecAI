FROM python:3.11-slim

WORKDIR /app

# libpq-dev: required to compile asyncpg
# build-essential: required for native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensures 'from app.X import Y' works in alembic/env.py and everywhere else
ENV PYTHONPATH=/app