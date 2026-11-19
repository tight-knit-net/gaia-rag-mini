FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src
WORKDIR /app
# S9.1: Debian official trixie-security fix for CVE-2026-85091.
# APT package VERSION is pinned; this does not waive other HIGH findings.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends 'zlib1g=1:1.3.dfsg+really1.3.1-1+deb13u1'; \
    rm -rf /var/lib/apt/lists/*
COPY requirements.lock ./
RUN pip install --no-cache-dir --require-hashes --only-binary=:all: -r requirements.lock \
    && python -m pip check \
    && useradd --uid 10001 --create-home --shell /usr/sbin/nologin gaia
COPY src/ ./src/
COPY app/ ./app/
COPY skills/gaia-rag-processos-administrativos/ ./skills/gaia-rag-processos-administrativos/
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=3s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz',timeout=2).read()" || exit 1
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
