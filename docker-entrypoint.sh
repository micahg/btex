#!/bin/sh
set -e

# Generate crontab for btex user from environment variable
# File was pre-created in Dockerfile with proper permissions
echo "${CRON_SCHEDULE} cd /app && python3 btex.py >> /proc/1/fd/1 2>&1" > /etc/crontabs/btex

echo "Cron schedule set to: ${CRON_SCHEDULE}"
cat /etc/crontabs/btex

# Start crond without foreground mode to avoid setpgid issues
# Then keep container alive
crond -l 2
echo "crond started in background, container will stay running..."

# Keep container running
exec tail -f /dev/null
