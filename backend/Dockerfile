FROM python:3.11-slim

# Install system dependencies for PostgreSQL and PostGIS
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements from backend subdirectory
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ .

# CRITICAL FIX: Copy GDELT data from project root
# Now accessible because build context is "." not "backend/"
COPY data/ /app/data

# Expose port
EXPOSE 8000

# Run with uvicorn, binding to Render's $PORT if set, otherwise 8000 (for local dev)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
