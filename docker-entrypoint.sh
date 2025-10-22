#!/bin/sh
set -e

# Generate crontab for btex user from environment variable
echo "${CRON_SCHEDULE} cd /app && python3 btex.py >> /proc/1/fd/1 2>&1" | crontab -u btex -

echo "Cron schedule set to: ${CRON_SCHEDULE}"
crontab -u btex -l

# Execute the CMD (crond will run as root but execute jobs as the btex user)
exec "$@"
