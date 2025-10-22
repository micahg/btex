#!/bin/sh
set -e

# Generate crontab for btex user from environment variable
echo "${CRON_SCHEDULE} cd /app && python3 btex.py >> /proc/1/fd/1 2>&1" > /etc/crontabs/btex

# Set proper ownership and permissions for crontab file
chown btex:btex /etc/crontabs/btex
chmod 0600 /etc/crontabs/btex

echo "Cron schedule set to: ${CRON_SCHEDULE}"
cat /etc/crontabs/btex

# Start crond without foreground mode to avoid setpgid issues
# -l 2: log level 2 (default, logs errors)
# -L /dev/stdout: log to stdout so Docker captures it
crond -l 2 -L /dev/stdout
echo "crond started in background, container will stay running..."

# Keep container running
exec tail -f /dev/null
