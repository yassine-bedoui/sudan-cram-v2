FROM python:3.11-slim

# Install system dependencies for PostgreSQL, PostGIS, and build tools (needed by prophet/cmdstanpy)
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    make \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements from backend subdirectory
COPY backend/requirements.txt .

# Install Python dependencies (this includes prophet)
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ .

# Copy data (GDELT, etc.)
COPY data/ /app/data

# Expose port
EXPOSE 8000

# Run with uvicorn, binding to Render's $PORT if set, otherwise 8000 (for local dev)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
