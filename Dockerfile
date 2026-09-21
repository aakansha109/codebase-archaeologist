# Production FastAPI Backend Container
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy full application codebase including src/
COPY . .

# Install Python packages & application package
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir .

# Create persistent workspace directories
RUN mkdir -p /app/qdrant_db /app/repos

ENV PORT=8000
EXPOSE 8000

# Launch FastAPI REST Server (supporting Railway dynamic PORT)
CMD ["sh", "-c", "uvicorn archaeologist.api.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
