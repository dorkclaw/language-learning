#syntax=docker/dockerfile:1
FROM python:3.13-slim

WORKDIR /app

# Install curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency install
RUN pip install uv

# Copy pyproject.toml first (for dependency caching)
COPY pyproject.toml uv.lock* .env.example* ./

# Install Python dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/

ENV PYTHONUNBUFFERED=1

# One-shot run: execute once and exit.
# Schedule via external cron (e.g. OpenClaw cron, system cron, docker-compose cron).
CMD ["uv", "run", "python", "-m", "src.bbc_noticias.bot"]
