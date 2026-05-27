# payment_gateway — imagem multi-stage (base compartilhada + dev / produção)
#
# Produção (padrão — sem --reload):
#   docker build -t payment_gateway:latest .
#   docker build --target production -t payment_gateway:latest .
#
# Desenvolvimento (hot-reload com --reload):
#   docker build --target dev -t payment_gateway:dev .
#   docker build --target dev --build-arg ENVIRONMENT=dev -t payment_gateway:dev .
#
# Compose / CI: use --target production ou --target dev conforme o ambiente.

FROM python:3.11-slim AS base

WORKDIR /app

COPY requirements.txt .

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY app app

# Criar diretórios necessários
RUN mkdir -p /data/sqlite/gateway /logs /backups

EXPOSE 8000

# ---------------------------------------------------------------------------
# Desenvolvimento: uvicorn com --reload
# ---------------------------------------------------------------------------
FROM base AS dev

ARG ENVIRONMENT=dev
ENV ENVIRONMENT=${ENVIRONMENT}

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---------------------------------------------------------------------------
# Produção (stage final / padrão): uvicorn sem --reload
# ---------------------------------------------------------------------------
FROM base AS production

ARG ENVIRONMENT=production
ENV ENVIRONMENT=${ENVIRONMENT}

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
