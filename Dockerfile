#syntax=docker/dockerfile:1
FROM python:3.13-slim

WORKDIR /app

# Install cron + curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
        cron curl ca-certificates bsdmainutils \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency install
RUN pip install uv

# Copy pyproject.toml first (for dependency caching)
COPY pyproject.toml uv.lock* .env.example* ./

# Install Python dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/

# Copy and install crontab (runs daily at 08:00 Berlin time)
# Copy crontab; cron reads /etc/cron.d automatically (no crontab install)
COPY crontab /etc/cron.d/bbc-noticias
RUN chmod 0644 /etc/cron.d/bbc-noticias

ENV PYTHONUNBUFFERED=1

# Container stays alive as cron daemon; bot is invoked by cron at 08:00 CET
CMD ["cron", "-f"]