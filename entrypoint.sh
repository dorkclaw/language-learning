#!/bin/bash
set -e

# Copy crontab to /etc/cron.d/ (bind-mount lands at /app/crontab)
cp /app/crontab /etc/cron.d/bbc-noticias
chmod 0644 /etc/cron.d/bbc-noticias

# Start cron daemon
exec cron -f