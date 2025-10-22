#!/bin/sh
set -e

# Create cron directory if it doesn't exist
mkdir -p /etc/crontabs

# Generate crontab for btex user from environment variable
echo "${CRON_SCHEDULE} cd /app && python3 btex.py >> /proc/1/fd/1 2>&1" > /etc/crontabs/btex

# Set proper permissions for crontab file
chmod 0600 /etc/crontabs/btex

echo "Cron schedule set to: ${CRON_SCHEDULE}"
cat /etc/crontabs/btex

# Execute the CMD (crond will run as root but execute jobs as the btex user)
exec "$@"
