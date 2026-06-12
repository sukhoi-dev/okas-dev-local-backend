# ── Stage 1: install deps ─────────────────────────────────────
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: secure runtime ───────────────────────────────────
FROM python:3.12-slim-bookworm

# Non-root user — containers should never run as root
RUN addgroup --system appgroup \
 && adduser  --system --ingroup appgroup --no-create-home appuser

WORKDIR /app

# Copy only installed packages from builder (no pip, no build tools)
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
