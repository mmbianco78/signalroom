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

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies (no dev extras in production)
RUN uv pip install --system --no-cache -e .

# -----------------------------------------------------------------------------
# Dependencies with browser support
# -----------------------------------------------------------------------------
FROM deps AS deps-browser

# Install Playwright dependencies and browsers
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

RUN uv pip install --system --no-cache playwright \
    && playwright install chromium

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
# Production image (API worker - no browser)
# -----------------------------------------------------------------------------
FROM deps AS prod

COPY . .
RUN chown -R app:app /app

USER app

CMD ["python", "-m", "signalroom.workers.main"]

# -----------------------------------------------------------------------------
# Production image (Browser worker)
# -----------------------------------------------------------------------------
FROM deps-browser AS prod-browser

COPY . .
RUN chown -R app:app /app

USER app

CMD ["python", "-m", "signalroom.workers.main", "--queue", "browser-tasks"]
