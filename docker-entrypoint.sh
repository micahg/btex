#!/bin/sh
set -e

# Generate crontab from environment variable
echo "${CRON_SCHEDULE} cd /app && python3 btex.py >> /proc/1/fd/1 2>&1" > /tmp/crontab
crontab /tmp/crontab

echo "Cron schedule set to: ${CRON_SCHEDULE}"
crontab -l

# Execute the CMD
exec "$@"
