#!/bin/bash
set -e

mkdir -p /app/shared
exec python -m src.bbc_noticias.discord_bot