# bayer-hackathon-2026 - FastAPI app
FROM python:3.11-slim

WORKDIR /app

# Install system deps if needed (e.g. for sentence-transformers / build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

ENV PATH="${POETRY_HOME}/bin:${PATH}"

# Copy dependency files first for better layer caching
COPY pyproject.toml poetry.lock ./

# Install dependencies (no dev)
RUN poetry install --only main --no-root

# Copy application code
COPY . .

# Non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
