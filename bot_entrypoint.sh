#!/bin/bash
set -e

mkdir -p /app/shared
exec /app/.venv/bin/python -m src.bbc_noticias.discord_bot