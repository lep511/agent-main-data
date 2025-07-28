FROM python:3.13-slim

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

EXPOSE 8080
WORKDIR /app

COPY . ./

RUN uv sync

# Add a simple health check endpoint test
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Use exec form to ensure proper signal handling
ENTRYPOINT ["uv", "run", "python", "-u", "main.py"]