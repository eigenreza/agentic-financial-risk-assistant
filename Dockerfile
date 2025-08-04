# ── Stage 1: build dependencies ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build tools needed for some packages (faiss, scipy, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies into an isolated prefix
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY app/        ./app/
COPY src/        ./src/
COPY data/       ./data/
COPY docs/       ./docs/

# Streamlit configuration: disable browser auto-open, set port
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# API key passed at runtime — never baked into the image
# docker run -e ANTHROPIC_API_KEY=your_key ...
ENV ANTHROPIC_API_KEY=""

EXPOSE 8501

# Health check: verify Streamlit is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

ENTRYPOINT ["python", "-m", "streamlit", "run", "app/streamlit_app.py", \
            "--server.port=8501", "--server.address=0.0.0.0"]
