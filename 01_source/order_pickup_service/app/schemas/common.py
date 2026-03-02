from datetime import datetime
from pydantic import BaseModel


class TimestampedSchema(BaseModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str


class IdResponse(BaseModel):
    id: int