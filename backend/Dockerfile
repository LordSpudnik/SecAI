FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install CPU-only PyTorch BEFORE requirements.txt
# --index-url forces pip to use the CPU-only wheel (~700MB vs ~2.5GB with CUDA)
# This must run before sentence-transformers — it checks if torch is present and uses it
RUN pip install --no-cache-dir \
    torch \
    --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app