FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY backend/ /app/
COPY agents/ /workspace/agents/
COPY rag/ /workspace/rag/
COPY scraper/ /workspace/scraper/

ENV PYTHONPATH=/app:/workspace
ENV PIP_DEFAULT_TIMEOUT=300

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
