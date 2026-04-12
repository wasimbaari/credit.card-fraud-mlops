# =========================
# 1️⃣ Builder Stage (Heavy)
# =========================
FROM python:3.10 AS builder

# Install system dependencies (for building packages)
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Upgrade pip tools + install dependencies into custom location
RUN pip install --upgrade pip setuptools wheel && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# =========================
# 2️⃣ Runtime Stage (Light)
# =========================
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Security updates + minimal runtime deps
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup -m appuser

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . /app

# Set permissions
RUN chown -R appuser:appgroup /app

USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Run app
CMD ["python", "src/training/train.py"]