from __future__ import annotations

from dataclasses import dataclass

try:
    from kafka.admin import KafkaAdminClient, NewTopic
except Exception:  # pragma: no cover - import guarded for envs without kafka
    KafkaAdminClient = None  # type: ignore[misc, assignment]
    NewTopic = None  # type: ignore[misc, assignment]


@dataclass(frozen=True)
class TopicSpec:
    name: str
    partitions: int = 3
    replication_factor: int = 1


DEFAULT_TOPICS: tuple[TopicSpec, ...] = (
    TopicSpec("catalog-stream"),
    TopicSpec("payment-stream"),
    TopicSpec("order-stream"),
    TopicSpec("wallet-stream"),
    TopicSpec("notification-stream"),
)


def ensure_topics(bootstrap_servers: str, topics: tuple[TopicSpec, ...] = DEFAULT_TOPICS) -> list[str]:
    if KafkaAdminClient is None or NewTopic is None:
        return [t.name for t in topics]
    admin_client = None
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            client_id="inventory-admin",
            request_timeout_ms=800,
        )
        existing = set(admin_client.list_topics())
        to_create = [NewTopic(t.name, t.partitions, t.replication_factor) for t in topics if t.name not in existing]
        if to_create:
            admin_client.create_topics(new_topics=to_create, validate_only=False)
        return [t.name for t in topics]
    except Exception:
        return [t.name for t in topics]
    finally:
        if admin_client is not None:
            try:
                admin_client.close()
            except Exception:
                pass
