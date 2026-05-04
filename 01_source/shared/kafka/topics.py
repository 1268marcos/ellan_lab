"""Constantes de tópicos e tipos de evento Kafka compartilhadas entre serviços."""

LOGISTICS_STREAM = "logistics-stream"
MANIFEST_CREATED = "manifest.created"
WALLET_CREDITED = "wallet.credited"
NOTIFICATION_SENT = "notification.sent"

DLQ_SUFFIX = ".dlq"


def dlq_stream(base_stream: str) -> str:
    return f"{base_stream}{DLQ_SUFFIX}"
