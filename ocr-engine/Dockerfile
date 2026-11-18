FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources && apt-get update && apt-get install -y --no-install-recommends \
  tesseract-ocr tesseract-ocr-por tesseract-ocr-eng poppler-utils fonts-dejavu-core \
  && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY engine.py api.py mcp_server.py restore.py ./
USER 65532:65532
EXPOSE 18788 18789
CMD ["uvicorn","api:app","--host","127.0.0.1","--port","18788"]
