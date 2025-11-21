FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Download MCP DatabaseToolbox (optional, can be mounted as volume)
ARG MCP_TOOLBOX_VERSION=0.20.0
RUN curl -L -o /usr/local/bin/toolbox \
    https://storage.googleapis.com/genai-toolbox/v${MCP_TOOLBOX_VERSION}/linux/amd64/toolbox && \
    chmod +x /usr/local/bin/toolbox || true

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy Poetry files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (use Poetry if lock file exists, otherwise fallback to requirements.txt)
RUN if [ -f poetry.lock ]; then \
        poetry config virtualenvs.create false && \
        poetry install --no-interaction --no-ansi; \
    else \
        if [ -f requirements.txt ]; then \
            pip install --no-cache-dir -r requirements.txt; \
        else \
            poetry config virtualenvs.create false && \
            poetry install --no-interaction --no-ansi; \
        fi; \
    fi

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Default command (can be overridden in docker-compose)
CMD ["python", "-m", "slack_bot.handler"]

