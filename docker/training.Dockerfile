# docker/training.Dockerfile
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Create a non-root user and group
RUN groupadd -r appgroup && useradd -r -g appgroup -m appuser

# Set working directory
WORKDIR /app

# Install dependencies (do this before copying code for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code and set ownership
COPY . /app
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Default command
CMD ["python", "src/training/train.py"]