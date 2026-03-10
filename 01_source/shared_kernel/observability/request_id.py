from contextvars import ContextVar
from uuid import uuid4

_request_id: ContextVar[str] = ContextVar("request_id", default="")


def set_request_id(value: str | None = None) -> str:
    rid = value or str(uuid4())
    _request_id.set(rid)
    return rid


def get_request_id() -> str:
    return _request_id.get() or ""


def clear_request_id() -> None:
    _request_id.set("")
