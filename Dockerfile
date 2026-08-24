# Build & Runtime Stage
FROM python:3.10-slim

# Install system dependencies (Git, build essentials)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition
COPY pyproject.toml requirements.txt ./

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e .

# Copy application source code
COPY . .

# Create persistent storage directories
RUN mkdir -p /app/qdrant_db /app/repos

# Expose Streamlit default port
EXPOSE 8501

# Health check endpoint
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Launch Streamlit server
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
