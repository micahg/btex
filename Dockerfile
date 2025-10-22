# Use Python 3 Alpine image as base
FROM python:3-alpine

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    p7zip

# Copy requirements first for better Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY btex.py .
COPY btextest.py .
COPY README.md .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV DEST_PATH=/srv
ENV SRC_PATH=/src

# Create necessary directories and non-root user for security
RUN mkdir -p /srv /src && \
    adduser -D -u 1000 btex && \
    chown -R btex:btex /app /srv /src

USER btex

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import btex; print('OK')" || exit 1

# Default command
CMD ["python3", "btex.py"]