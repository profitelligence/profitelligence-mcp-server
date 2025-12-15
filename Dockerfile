# Multi-stage Dockerfile for Profitelligence MCP Server
# Stage 1: Build stage
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

# Stage 2: Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY src/ ./src/
COPY config/ ./config/

# Create non-root user
RUN useradd -m -u 1000 mcp && \
    chown -R mcp:mcp /app

USER mcp

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PROF_MCP_MODE=stdio

# Expose port for HTTP mode (optional)
EXPOSE 3000

# Health check for HTTP mode - use root path since /health may not exist
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:3000/')" || exit 1

# Entry point supports both stdio and HTTP modes
ENTRYPOINT ["python", "-m", "src.server"]

# Default to stdio mode (can be overridden with --http flag)
CMD []
