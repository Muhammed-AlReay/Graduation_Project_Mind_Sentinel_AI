FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config.py ingest.py llm_router.py main.py ./
COPY memory/ memory/
COPY retrieval/ retrieval/
COPY safety/ safety/
COPY utils/ utils/
COPY service/ service/
COPY data/ data/

ENV PROJECT12_BASE_DIR=/app
ENV PROJECT12_AUTO_INGEST=true
ENV PROJECT12_HOST=0.0.0.0
ENV PROJECT12_PORT=8100
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface

RUN mkdir -p /app/memory_data /app/vectorstore /app/.cache/huggingface

EXPOSE 8100

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8100/health')" || exit 1

CMD ["python", "-m", "uvicorn", "service.app:app", "--host", "0.0.0.0", "--port", "8100"]
