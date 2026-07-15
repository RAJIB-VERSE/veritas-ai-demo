# Use a slim Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (for Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full project
COPY . .

# Create necessary directories
RUN mkdir -p instance saved_models data

# Set environment variables for production
ENV FLASK_CONFIG=production
ENV PYTHONUNBUFFERED=1
# HuggingFace Spaces runs on port 7860
ENV PORT=7860

# Expose port
EXPOSE 7860

# Run with gunicorn for production
CMD ["python", "-c", "from app import create_app; from waitress import serve; app = create_app('production'); serve(app, host='0.0.0.0', port=7860)"]
