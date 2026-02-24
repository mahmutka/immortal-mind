FROM python:3.13-slim

WORKDIR /app

# System deps (chromadb needs build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agent/       agent/
COPY cognitio/    cognitio/
COPY storage/     storage/
COPY frontend/    frontend/
COPY contracts/   contracts/

# Runtime data directory (mount Lightsail block storage here)
RUN mkdir -p data

# Suppress HuggingFace noise
ENV TOKENIZERS_PARALLELISM=false
ENV HF_HUB_DISABLE_PROGRESS_BARS=1

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["python", "-m", "streamlit", "run", "frontend/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
