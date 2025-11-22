FROM python:3.11-slim

# Install system dependencies for PostgreSQL and building psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python dependencies list from backend subdirectory
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ .

# Copy data directory (e.g. GDELT, ACLED, etc.) from project root into the image
COPY data/ /app/data

# Expose backend port
EXPOSE 8000

# Run FastAPI app with uvicorn
# Uses $PORT if set (e.g. on Render), otherwise defaults to 8000 for local dev
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
