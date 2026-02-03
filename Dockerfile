# Use Python 3 Slim (Debian) image for better unrar compatibility
FROM python:3-slim-bookworm

# Set working directory
WORKDIR /app

# Enable non-free repositories and install unrar
# We rewrite sources.list to ensure we have non-free components for unrar
RUN echo "deb http://deb.debian.org/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    unrar \
    && rm -rf /var/lib/apt/lists/*

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
# Debian uses useradd
RUN mkdir -p /srv /src && \
    useradd -u 1000 -U -m -s /bin/bash btex && \
    chown -R btex:btex /app /srv /src

# Switch to non-root user
USER btex

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import btex; print('OK')" || exit 1

# Run the application directly
CMD ["python3", "btex.py"]
