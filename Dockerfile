# Use official Python image with slim-buster
FROM python:3.11-slim-bookworm AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR 1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY pyproject.toml .
COPY requirements.txt .

# Install dependencies globally
RUN pip install --no-warn-script-location -r requirements.txt

# Copy the rest of the application
COPY . .

# --- Runtime stage ---
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONPATH=/app

# Copy installed dependencies from builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

# Set work directory
WORKDIR /app

# Create non-root user and switch to it
RUN useradd -m myuser && chown -R myuser:myuser /app
USER myuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
