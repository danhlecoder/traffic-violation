FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=600 \
    PIP_RETRIES=5

WORKDIR /app

# System deps for OpenCV/FFmpeg runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender1 libgl1 \
 && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY requirements.txt /app/requirements.txt

# Install with high timeout and retries for large CUDA packages
RUN pip install --no-cache-dir \
    --timeout=600 \
    --retries=5 \
    --prefer-binary \
    -r /app/requirements.txt

# Copy backend code (this layer will be rebuilt when code changes)
COPY backend /app/backend

EXPOSE 8000

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

