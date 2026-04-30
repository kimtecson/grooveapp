# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /install /usr/local
COPY app.py .

# Non-root user for security
RUN useradd -m appuser
USER appuser

EXPOSE 5000

# Gunicorn: 4 workers, bind to 0.0.0.0:5000
# In ECS the ALB/Nginx terminates TLS; Gunicorn runs on 5000 internally
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "--timeout", "120", "app:app"]
