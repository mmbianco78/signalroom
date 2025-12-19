# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# -----------------------------------------------------------------------------
# Dependencies stage - install Python packages
# -----------------------------------------------------------------------------
FROM base AS deps

# Copy dependency files and source for installation
COPY pyproject.toml ./
COPY src/ ./src/

# Install dependencies (no dev extras in production)
RUN uv pip install --system --no-cache -e .

# -----------------------------------------------------------------------------
# Development image
# -----------------------------------------------------------------------------
FROM deps AS dev

# Install dev dependencies
RUN uv pip install --system --no-cache -e ".[dev]"

COPY . .
RUN chown -R app:app /app

USER app

CMD ["python", "-m", "signalroom.workers.main"]

# -----------------------------------------------------------------------------
# Production image
# -----------------------------------------------------------------------------
FROM deps AS prod

COPY . .
RUN chown -R app:app /app

USER app

CMD ["python", "-m", "signalroom.workers.main"]
