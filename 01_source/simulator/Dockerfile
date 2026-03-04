FROM python:3.11-slim

# Logs imediatos + pip mais previsível
ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependências do healthcheck (mosquitto_pub/sub)
RUN apt-get update \
    && apt-get install -y --no-install-recommends mosquitto-clients ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Dependências Python
COPY requirements.txt .
RUN pip install -r requirements.txt

# Código
COPY app app

# Usuário não-root (boa prática)
RUN useradd -m -u 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

# Healthcheck:
#  - tenta publicar 1 mensagem "PING" num tópico de health
#  - falha se não conseguir conectar no broker
# Obs: MQTT_HOST precisa estar setado no container (no seu compose já está).
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
  CMD sh -lc 'mosquitto_pub -h "${MQTT_HOST:-mqtt_broker}" -p "${MQTT_PORT:-1883}" -t "locker/${REGION:-SP}/simulator/health" -m "{\"ts\":$(date +%s),\"status\":\"PING\"}" >/dev/null 2>&1 || exit 1'

CMD ["python", "-u", "app/main.py"]