from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.notification import Notification
from app.services import queue_consumer

router = APIRouter(prefix="/api/v1", tags=["notifications"])


class QueueIn(BaseModel):
    channel: str = Field(pattern="^(email|sms|whatsapp)$")
    payload: str
    order_id: str = "unknown"


@router.post("/queue", status_code=status.HTTP_201_CREATED)
def post_queue(body: QueueIn, request: Request, db: Session = Depends(get_db)) -> dict:
    r = getattr(request.app.state, "redis", None)
    n = Notification(channel=body.channel, payload=body.payload, status="queued")
    db.add(n)
    db.commit()
    db.refresh(n)
    queue_consumer.enqueue(r, "notification:queue", {"id": n.id, "order_id": body.order_id})
    return {"id": n.id, "status": n.status}


@router.get("/status/{notification_id}")
def get_status(notification_id: str, db: Session = Depends(get_db)) -> dict:
    n = db.get(Notification, notification_id)
    if not n:
        raise HTTPException(status_code=404, detail="not_found")
    return {"id": n.id, "status": n.status, "attempts": n.attempts, "last_error": n.last_error}
