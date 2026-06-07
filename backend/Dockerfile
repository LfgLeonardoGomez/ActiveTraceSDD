# Multi-stage Dockerfile para activia-trace backend
# Convención Easypanel: runtime sin toolchain de build

# ── Stage 1: builder ─────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

# Copiar archivos de dependencias y código mínimo para instalar
COPY pyproject.toml ./
COPY app/__init__.py ./app/__init__.py

# Instalar dependencias en un entorno virtual (no editable para evitar bind mount)
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python -e "."

# ── Stage 2: runtime ─────────────────────────────────────────────
FROM python:3.13-slim AS runtime

WORKDIR /app

# Copiar entorno virtual del builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar código de la aplicación
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Puerto de la aplicación
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Arranque con uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
