#!/bin/bash
set -e

# Shared volume path for cron → bot communication
mkdir -p /app/shared

# Copy crontab to /etc/cron.d/ (bind-mount lands at /app/crontab)
cp /app/crontab /etc/cron.d/bbc-noticias
chmod 0644 /etc/cron.d/bbc-noticias

# Export shared queue path so Python modules can find it
export SHARED_QUEUE_PATH=/app/shared/queue.json

# Start cron daemon
exec cron -f