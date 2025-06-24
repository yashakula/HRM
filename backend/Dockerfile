# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Copy uv configuration files and README
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy application code
COPY src/ ./src/

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uv", "run", "uvicorn", "hrm_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]