#syntax=docker/dockerfile:1
FROM python:3.13-slim

WORKDIR /app

ENV TZ=Europe/Berlin

# Install cron + curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron curl ca-certificates bsdmainutils tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

# Install uv for fast dependency install
RUN pip install uv

# Copy pyproject.toml first (for dependency caching)
COPY pyproject.toml uv.lock* .env.example* ./

# Install Python dependencies
RUN uv sync --no-dev

# Copy application code
COPY src/ ./src/

# Copy entrypoint script (validates crontab before starting cron)
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENV PYTHONUNBUFFERED=1

# Container stays alive as cron daemon; bot is invoked by cron at 08:00 CET
CMD ["cron", "-f"]