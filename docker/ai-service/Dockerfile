# ci-trigger-5
# ================================================================
# AI-Travel: ai-service Production Dockerfile
# Base: python:3.12-slim | Port: 8000 | User: appuser
# ================================================================

# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install runtime OS dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    chown -R appuser:appuser /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Switch to non-root user before copying code
USER appuser

# Copy application code
COPY --chown=appuser:appuser app/ ./app/

# Environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH=/home/appuser/.local/bin:$PATH

# Expose service port
EXPOSE 8000

# Health check using curl (ai-service is stateless)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Graceful shutdown signal
STOPSIGNAL SIGTERM

# Run with gunicorn + uvicorn workers for production
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--keep-alive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "app.main:app"]
