#!/bin/bash
set -e

# Copy crontab to /etc/cron.d/ (bind-mount lands at /app/crontab)
cp /app/crontab /etc/cron.d/bbc-noticias
chmod 0644 /etc/cron.d/bbc-noticias

# Validate crontab syntax before starting cron
if ! cron -T -n 2>/dev/null; then
    echo "ERROR: crontab validation failed" >&2
    exit 1
fi

# Start cron daemon
exec cron -f